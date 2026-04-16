"""
F.A.R.O. Mobile API - fluxo do agente de campo.
"""
import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.core.observability import record_feedback_pending, record_sync_batch
from app.db.base import (
    AnalystFeedbackEvent,
    FeedbackEvent,
    IntelligenceReview,
    PlateRead,
    SuspicionReport,
    SyncStatus,
    Asset,
    Unit,
    User,
    UserRole,
    VehicleObservation,
)
from app.schemas.common import GeolocationPoint, PaginationParams
from app.schemas.intelligence import FeedbackForAgent
from app.schemas.observation import (
    ApproachConfirmationRequest,
    ApproachConfirmationResponse,
    ObservationHistoryItem,
    ObservationHistoryResponse,
    OcrValidationRequest,
    OcrValidationResponse,
    PlateSuspicionCheckResponse,
    VehicleObservationCreate,
    VehicleObservationResponse,
)
from app.schemas.suspicion import SuspicionReportCreate, SuspicionReportResponse
from app.schemas.sync import SyncBatchRequest, SyncBatchResponse, SyncResult
from app.services.observation_service import (
    fetch_history_flags,
    get_or_register_device,
    location_geometry,
    serialize_observation,
)
from app.services.operational_context_service import (
    build_operational_context_for_observation,
    get_first_prior_suspicion_for_plate,
)
from app.services.analytics_service import evaluate_observation_algorithms
from app.services.audit_service import log_audit_event
from app.services.event_bus import event_bus
from app.services.feedback_service import fetch_pending_feedback_for_user
from app.services.ocr_service import get_ocr_service
from app.services.storage_service import (
    complete_progressive_upload,
    upload_observation_asset_bytes,
    upload_observation_asset_progressive,
)

router = APIRouter()


def require_field_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {
        UserRole.FIELD_AGENT,
        UserRole.INTELLIGENCE,
        UserRole.SUPERVISOR,
        UserRole.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso operacional de campo requerido",
        )
    return current_user


@router.post("/observations", response_model=VehicleObservationResponse)
async def create_observation(
    payload: VehicleObservationCreate,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    if payload.client_id:
        existing_result = await db.execute(
            select(VehicleObservation).where(VehicleObservation.client_id == payload.client_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return await serialize_observation(db, existing, current_user)

    device = await get_or_register_device(
        db,
        device_identifier=payload.device_id,
        current_user=current_user,
        app_version=payload.app_version,
    )

    observation = VehicleObservation(
        client_id=payload.client_id,
        agent_id=current_user.id,
        agency_id=current_user.agency_id,
        device_id=device.id,
        plate_number=payload.plate_number,
        plate_state=payload.plate_state,
        plate_country=payload.plate_country,
        observed_at_local=payload.observed_at_local,
        observed_at_server=datetime.utcnow(),
        location=location_geometry(payload.location),
        location_accuracy=payload.location.accuracy,
        heading=payload.heading,
        speed=payload.speed,
        vehicle_color=payload.vehicle_color,
        vehicle_type=payload.vehicle_type,
        vehicle_model=payload.vehicle_model,
        vehicle_year=payload.vehicle_year,
        connectivity_type=payload.connectivity_type,
        sync_status=SyncStatus.COMPLETED,
        synced_at=datetime.utcnow(),
        metadata_snapshot={
            "origin": "mobile",
            "device_id": payload.device_id,
            "app_version": payload.app_version,
            "connectivity_type": payload.connectivity_type or "unknown",
        },
    )
    db.add(observation)
    await db.flush()

    if payload.plate_read is not None:
        db.add(
            PlateRead(
                observation_id=observation.id,
                ocr_raw_text=payload.plate_read.ocr_raw_text,
                ocr_confidence=payload.plate_read.ocr_confidence,
                ocr_engine=payload.plate_read.ocr_engine,
                image_width=payload.plate_read.image_width,
                image_height=payload.plate_read.image_height,
                processing_time_ms=payload.plate_read.processing_time_ms,
            )
        )

    await db.flush()
    await evaluate_observation_algorithms(db, observation)
    operational_context = await build_operational_context_for_observation(
        db,
        observation=observation,
    )
    observation.metadata_snapshot = {
        **(observation.metadata_snapshot or {}),
        "state_registry_status": operational_context.get("state_registry"),
        "prior_suspicion_context": operational_context.get("prior_suspicion"),
    }
    await event_bus.publish(
        "observation_created",
        {
            "payload_version": "v1",
            "observation_id": str(observation.id),
            "agent_id": str(current_user.id),
            "plate_number": observation.plate_number,
            "source": "mobile_online",
        },
    )
    await log_audit_event(
        db,
        actor=current_user,
        action="observation_created",
        resource_type="vehicle_observation",
        resource_id=observation.id,
        details={
            "plate_number": observation.plate_number,
            "client_id": observation.client_id,
            "sync_status": observation.sync_status.value,
        },
    )
    return await serialize_observation(
        db,
        observation,
        current_user,
        operational_context=operational_context,
    )


@router.get("/history", response_model=ObservationHistoryResponse)
async def get_observation_history(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.count(VehicleObservation.id)).where(VehicleObservation.agent_id == current_user.id)
    )
    pending_result = await db.execute(
        select(func.count(VehicleObservation.id)).where(
            and_(
                VehicleObservation.agent_id == current_user.id,
                VehicleObservation.sync_status != SyncStatus.COMPLETED,
            )
        )
    )
    observations_result = await db.execute(
        select(VehicleObservation)
        .where(VehicleObservation.agent_id == current_user.id)
        .order_by(desc(VehicleObservation.observed_at_local))
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    observations = observations_result.scalars().all()
    observation_ids = [observation.id for observation in observations]
    feedback_map, suspicion_map = await fetch_history_flags(db, observation_ids)

    items: list[ObservationHistoryItem] = []
    for observation in observations:
        point = to_shape(observation.location)
        items.append(
            ObservationHistoryItem(
                id=observation.id,
                client_id=observation.client_id,
                plate_number=observation.plate_number,
                observed_at_local=observation.observed_at_local,
                location=GeolocationPoint(
                    latitude=point.y,
                    longitude=point.x,
                    accuracy=observation.location_accuracy,
                ),
                sync_status=observation.sync_status,
                has_feedback=feedback_map.get(observation.id, False),
                has_suspicion=suspicion_map.get(observation.id, False),
            )
        )

    return ObservationHistoryResponse(
        items=items,
        pending_sync_count=pending_result.scalar() or 0,
        total_count=total_result.scalar() or 0,
    )


@router.get("/plates/{plate_number}/check-suspicion", response_model=PlateSuspicionCheckResponse)
async def check_plate_suspicion(
    plate_number: str,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    """Check if a plate has suspicion indicators (for post-OCR alert in mobile app).
    
    TODO[FUTURO - OUTRO DEV]: Integrar consulta a bases de dados oficiais
    -----------------------------------------------------------------------------
    Este endpoint verifica suspeitas internas (watchlist, suspeitas anteriores).
    Deve ser expandido para consultar:
    
    1. BASE ESTADUAL (DETRAN-MS): Roubo/furto, débitos, restrições
       - Adapter: app/integrations/state_registry_adapter.py
       - Implementar: query_state_vehicle_registry() com conexão real
       - Endpoint externo: A definir pela BMRS
       
    2. POLÍCIA FEDERAL: Veículos com alertas nacionais
       - Criar novo adapter: federal_police_adapter.py
       - Requer credenciais e certificação digital ICP-Brasil
       
    3. BASE NACIONAL DE VEÍCULOS RENAVAM: Dados cadastrais
       - Criar adapter: renavam_adapter.py
       - Dados: proprietário, situação, licenciamento
       
    RETORNO AO AGENTE: Incluir os dados oficiais na resposta quando disponíveis.
    Ver campos opcionais no schema PlateSuspicionCheckResponse para expansão.
    -----------------------------------------------------------------------------
    """
    from app.services.operational_context_service import (
        get_first_prior_suspicion_for_plate,
        count_recent_observations,
    )
    from app.db.base import WatchlistEntry, WatchlistStatus
    from sqlalchemy import func
    
    # Normalize plate
    normalized_plate = plate_number.upper().replace(" ", "").replace("-", "").strip()
    agency_id = current_user.agency_id
    
    # =========================================================================
    # TODO[FUTURO]: CHAMADA À BASE ESTADUAL (DETRAN/POLÍCIA)
    # =========================================================================
    # from app.integrations.state_registry_adapter import query_state_vehicle_registry
    # official_data = await query_state_vehicle_registry(plate_number=normalized_plate)
    # 
    # Usar dados oficiais para enriquecer a resposta:
    # - Marcar suspeita se veículo consta como roubado/furtado
    # - Incluir dados do proprietário (se autorizado)
    # - Alertar sobre débitos/restrições administrativas
    # =========================================================================
    
    # Check watchlist, prior suspicion, and count previous observations in parallel
    # REGRA: Agente de campo ve watchlist de TODAS as agencias (visibilidade ampla)
    # REGRA: Agente de campo ve suspeitas de TODAS as agencias
    # REGRA: Conta observacoes de TODAS as agencias (contexto completo)
    watchlist_result, prior_context, previous_count = await asyncio.gather(
        db.execute(
            select(WatchlistEntry).where(
                and_(
                    WatchlistEntry.plate_number == normalized_plate,
                    WatchlistEntry.status == WatchlistStatus.ACTIVE,
                )
            )
        ),
        get_first_prior_suspicion_for_plate(
            db,
            plate_number=normalized_plate,
            agency_id=None,  # Sem filtro de agencia - visao ampla
            exclude_observation_id=None,
        ),
        count_recent_observations(
            db,
            plate_number=normalized_plate,
            agency_id=None,  # Sem filtro de agencia
            days=30,
        )
    )
    watchlist_entry = watchlist_result.scalar_one_or_none()
    
    # Determine if suspect
    is_suspect = watchlist_entry is not None or (prior_context and prior_context.get("has_prior_suspicion"))
    
    if not is_suspect:
        return PlateSuspicionCheckResponse(
            plate_number=normalized_plate,
            is_suspect=False,
            previous_observations_count=previous_count,
        )
    
    # Build alert based on priority
    alert_level = "warning"
    alert_title = "Veiculo com Indicativos"
    suspicion_reason = None
    suspicion_level = None
    watchlist_category = None
    requires_approach = False
    guidance = "Proceder com atencao. Registrar observacao estruturada se comportamento suspeito confirmado."
    
    if watchlist_entry:
        alert_level = "critical" if watchlist_entry.priority >= 4 else "warning"
        alert_title = f"WATCHLIST: {watchlist_entry.category.value.replace('_', ' ').upper()}"
        watchlist_category = watchlist_entry.category.value
        suspicion_reason = watchlist_entry.notes
        requires_approach = watchlist_entry.requires_approach
        if watchlist_entry.approach_guidance:
            guidance = watchlist_entry.approach_guidance
    
    if prior_context and prior_context.get("has_prior_suspicion"):
        suspicion_reason = prior_context.get("first_suspicion_reason")
        suspicion_level = prior_context.get("first_suspicion_level")
        if prior_context.get("first_suspicion_urgency") == "approach":
            alert_level = "critical"
            requires_approach = True
        alert_title = "SUSPEITA PREVIA REGISTRADA"
    
    # Build alert message
    alert_parts = [f"Placa {normalized_plate} possui registros previos."]
    if watchlist_category:
        alert_parts.append(f"Categoria: {watchlist_category.replace('_', ' ').upper()}.")
    if suspicion_reason:
        alert_parts.append(f"Motivo: {suspicion_reason}.")
    if previous_count > 0:
        alert_parts.append(f"Passagens recentes: {previous_count}.")
    
    if requires_approach:
        alert_parts.append("ABORDAGEM RECOMENDADA conforme diretrizes.")
        guidance = "Confirmar suspeita e registrar desfecho da abordagem."
    
    return PlateSuspicionCheckResponse(
        plate_number=normalized_plate,
        is_suspect=True,
        alert_level=alert_level,
        alert_title=alert_title,
        alert_message=" ".join(alert_parts),
        suspicion_reason=suspicion_reason,
        suspicion_level=suspicion_level,
        previous_observations_count=previous_count,
        is_monitored=watchlist_entry is not None and watchlist_entry.category.value == "monitored_vehicle",
        intelligence_interest=prior_context is not None and prior_context.get("has_prior_suspicion"),
        has_active_watchlist=watchlist_entry is not None,
        watchlist_category=watchlist_category,
        guidance=guidance,
        requires_approach_confirmation=requires_approach,
        first_suspicion_agent_name=prior_context.get("first_suspicion_agent_name") if prior_context else None,
        first_suspicion_observation_id=UUID(prior_context["first_suspicion_observation_id"]) if prior_context and prior_context.get("first_suspicion_observation_id") else None,
        first_suspicion_at=prior_context.get("first_suspicion_at") if prior_context else None,
    )


@router.post("/ocr/validate", response_model=OcrValidationResponse)
async def validate_ocr(
    payload: OcrValidationRequest,
    current_user: User = Depends(require_field_agent),
):
    """
    Validate OCR result using backend YOLOv11 + EasyOCR.
    
    Mobile app can send images for reprocessing when online.
    Backend uses more powerful models to validate or improve mobile OCR.
    
    This is optional - mobile can work offline with local OCR.
    Backend validation is for quality assurance and model improvement.
    """
    import base64
    from io import BytesIO
    
    # Decode base64 image
    try:
        image_bytes = base64.b64decode(payload.image_base64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 image: {str(e)}"
        )
    
    # Get OCR service
    ocr_service = get_ocr_service()
    
    # Process image with backend OCR
    result = ocr_service.process_image_bytes(
        image_bytes=image_bytes,
        confidence_threshold=payload.confidence_threshold
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OCR processing failed - no plate detected"
        )
    
    # Validate plate format
    is_valid, plate_format = ocr_service.validate_plate_number(result.plate_number)
    
    # Compare with mobile OCR if provided
    mobile_comparison = None
    improved_over_mobile = False
    
    if payload.mobile_ocr_text:
        mobile_comparison = {
            "mobile_text": payload.mobile_ocr_text,
            "mobile_confidence": payload.mobile_ocr_confidence,
            "backend_text": result.plate_number,
            "backend_confidence": result.confidence,
            "match": payload.mobile_ocr_text.upper().replace(" ", "").replace("-", "") == result.plate_number
        }
        
        # Consider improved if backend confidence is significantly higher
        if payload.mobile_ocr_confidence and result.confidence > payload.mobile_ocr_confidence + 0.1:
            improved_over_mobile = True
    
    return OcrValidationResponse(
        plate_number=result.plate_number,
        confidence=result.confidence,
        plate_format=result.plate_format,
        processing_time_ms=result.processing_time_ms,
        ocr_engine=result.ocr_engine,
        is_valid_format=is_valid,
        improved_over_mobile=improved_over_mobile,
        mobile_comparison=mobile_comparison
    )


@router.post("/observations/{observation_id}/suspicion", response_model=SuspicionReportResponse)
async def add_suspicion_report(
    observation_id: UUID,
    payload: SuspicionReportCreate,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    observation_result = await db.execute(
        select(VehicleObservation).where(
            and_(
                VehicleObservation.id == observation_id,
                VehicleObservation.agent_id == current_user.id,
            )
        )
    )
    observation = observation_result.scalar_one_or_none()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")

    existing_result = await db.execute(
        select(SuspicionReport).where(SuspicionReport.observation_id == observation_id)
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Observacao ja possui suspeicao registrada")

    report = SuspicionReport(
        observation_id=observation_id,
        reason=payload.reason,
        level=payload.level,
        urgency=payload.urgency,
        notes=payload.notes,
        audio_duration_seconds=payload.audio_duration_seconds,
    )
    db.add(report)
    await db.flush()
    await event_bus.publish(
        "suspicion_submitted",
        {
            "payload_version": "v1",
            "observation_id": str(observation_id),
            "suspicion_report_id": str(report.id),
            "reason": report.reason.value,
            "level": report.level.value,
            "urgency": report.urgency.value,
        },
    )
    await log_audit_event(
        db,
        actor=current_user,
        action="suspicion_submitted",
        resource_type="suspicion_report",
        resource_id=report.id,
        details={
            "observation_id": str(observation_id),
            "reason": report.reason.value,
            "level": report.level.value,
            "urgency": report.urgency.value,
        },
        justification=report.notes,
    )

    return SuspicionReportResponse.model_validate(report)


@router.get("/observations/{observation_id}/feedback", response_model=list[FeedbackForAgent])
async def get_observation_feedback(
    observation_id: UUID,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    observation_result = await db.execute(
        select(VehicleObservation).where(
            and_(
                VehicleObservation.id == observation_id,
                VehicleObservation.agent_id == current_user.id,
            )
        )
    )
    observation = observation_result.scalar_one_or_none()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")

    structured_filters = [AnalystFeedbackEvent.target_user_id == current_user.id]
    unit_code = None
    if current_user.unit_id:
        unit = (
            await db.execute(select(Unit).where(Unit.id == current_user.unit_id))
        ).scalar_one_or_none()
        unit_code = unit.code if unit is not None else None
    if unit_code:
        structured_filters.append(AnalystFeedbackEvent.target_team_label == unit_code)

    structured_result = await db.execute(
        select(AnalystFeedbackEvent, User)
        .join(User, User.id == AnalystFeedbackEvent.analyst_id)
        .where(
            and_(
                AnalystFeedbackEvent.observation_id == observation_id,
                AnalystFeedbackEvent.agency_id == current_user.agency_id,
                or_(*structured_filters),
            )
        )
        .order_by(desc(AnalystFeedbackEvent.created_at))
    )

    legacy_result = await db.execute(
        select(FeedbackEvent, IntelligenceReview, User)
        .join(IntelligenceReview, FeedbackEvent.review_id == IntelligenceReview.id)
        .join(User, User.id == IntelligenceReview.reviewer_id)
        .where(IntelligenceReview.observation_id == observation_id)
        .order_by(desc(FeedbackEvent.sent_at))
    )

    merged_feedback = [
        FeedbackForAgent(
            feedback_id=feedback.id,
            observation_id=observation_id,
            plate_number=observation.plate_number,
            feedback_type=feedback.feedback_type,
            title=feedback.title,
            message=feedback.message,
            recommended_action=None,
            sent_at=feedback.delivered_at or feedback.created_at,
            is_read=feedback.read_at is not None,
            read_at=feedback.read_at,
            reviewer_name=analyst.full_name,
        )
        for feedback, analyst in structured_result.all()
    ]

    merged_feedback.extend([
        FeedbackForAgent(
            feedback_id=feedback.id,
            observation_id=observation_id,
            plate_number=observation.plate_number,
            feedback_type=feedback.feedback_type,
            title=feedback.title,
            message=feedback.message,
            recommended_action=feedback.recommended_action,
            sent_at=feedback.sent_at,
            is_read=feedback.read_at is not None,
            read_at=feedback.read_at,
            reviewer_name=reviewer.full_name,
        )
        for feedback, _, reviewer in legacy_result.all()
    ])
    merged_feedback.sort(key=lambda item: item.sent_at, reverse=True)
    return merged_feedback


@router.post(
    "/observations/{observation_id}/approach-confirmation",
    response_model=ApproachConfirmationResponse,
)
async def confirm_vehicle_approach(
    observation_id: UUID,
    payload: ApproachConfirmationRequest,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    observation_result = await db.execute(
        select(VehicleObservation).where(
            and_(
                VehicleObservation.id == observation_id,
                VehicleObservation.agent_id == current_user.id,
            )
        )
    )
    observation = observation_result.scalar_one_or_none()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")

    # Busca suspeita de QUALQUER agencia (para encontrar o cadastrador original)
    # REGRA: Retorno de abordagem (n+1) deve ir para agencia de origem + cadastrador original
    prior_context = await get_first_prior_suspicion_for_plate(
        db,
        plate_number=observation.plate_number,
        agency_id=None,  # Sem filtro de agencia - busca em todo o sistema
        exclude_observation_id=observation.id,
    )
    if not prior_context or not prior_context.get("has_prior_suspicion"):
        await log_audit_event(
            db,
            actor=current_user,
            action="approach_confirmation_recorded",
            resource_type="vehicle_observation",
            resource_id=observation.id,
            details={
                "confirmed_suspicion": payload.confirmed_suspicion,
                "approach_outcome": payload.approach_outcome,
                "notified_original_agent": False,
                "suspicion_level_slider": payload.suspicion_level_slider,
                "was_approached": payload.was_approached,
                "has_incident": payload.has_incident,
            },
            justification=payload.notes,
        )
        await event_bus.publish(
            "field_approach_confirmed",
            {
                "payload_version": "v1",
                "observation_id": str(observation.id),
                "plate_number": observation.plate_number,
                "confirmed_suspicion": payload.confirmed_suspicion,
                "approach_outcome": payload.approach_outcome,
                "notified_original_agent": False,
                "suspicion_level_slider": payload.suspicion_level_slider,
                "was_approached": payload.was_approached,
                "has_incident": payload.has_incident,
            },
        )
        return ApproachConfirmationResponse(
            observation_id=observation.id,
            plate_number=observation.plate_number,
            confirmed_suspicion=payload.confirmed_suspicion,
            approach_outcome=payload.approach_outcome,
            notified_original_agent=False,
            processed_at=datetime.utcnow(),
        )

    original_agent_id = UUID(prior_context["first_suspicion_agent_id"])
    original_agent_name = prior_context.get("first_suspicion_agent_name")
    original_agency_id = UUID(prior_context["first_suspicion_agency_id"])  # Agencia de origem
    observation_point = to_shape(observation.location)
    location_hint = (
        f"{payload.location.latitude:.6f}, {payload.location.longitude:.6f}"
        if payload.location is not None
        else f"{observation_point.y:.6f}, {observation_point.x:.6f}"
    )
    confirmation_label = "confirmada" if payload.confirmed_suspicion else "nao confirmada"
    message = (
        f"Abordagem registrada para placa {observation.plate_number}. "
        f"Suspeicao {confirmation_label}. "
        f"Local: {location_hint}. "
        f"Desfecho: {payload.approach_outcome}."
    )
    if payload.notes:
        message = f"{message} Observacao de campo: {payload.notes}"

    actor_unit_code = None
    if current_user.unit_id:
        actor_unit = (
            await db.execute(select(Unit).where(Unit.id == current_user.unit_id))
        ).scalar_one_or_none()
        actor_unit_code = actor_unit.code if actor_unit is not None else None

    # REGRA: Feedback vai para agencia de origem + cadastrador original
    feedback_event = AnalystFeedbackEvent(
        agency_id=original_agency_id,  # Agencia de inteligencia de origem
        observation_id=UUID(prior_context["first_suspicion_observation_id"]),
        analyst_id=current_user.id,
        target_user_id=original_agent_id,  # Cadastrador original
        target_team_label=actor_unit_code,
        feedback_type="approach_confirmation",
        sensitivity_level="operational",
        title=f"Retorno de abordagem da placa {observation.plate_number}",
        message=message,
        delivered_at=datetime.utcnow(),
    )
    db.add(feedback_event)
    await db.flush()

    await log_audit_event(
        db,
        actor=current_user,
        action="approach_confirmation_recorded",
        resource_type="vehicle_observation",
        resource_id=observation.id,
        details={
            "confirmed_suspicion": payload.confirmed_suspicion,
            "approach_outcome": payload.approach_outcome,
            "original_agent_id": str(original_agent_id),
            "feedback_event_id": str(feedback_event.id),
        },
        justification=payload.notes,
    )
    await event_bus.publish(
        "field_approach_confirmed",
        {
            "payload_version": "v1",
            "observation_id": str(observation.id),
            "plate_number": observation.plate_number,
            "confirmed_suspicion": payload.confirmed_suspicion,
            "approach_outcome": payload.approach_outcome,
            "original_agent_id": str(original_agent_id),
            "feedback_event_id": str(feedback_event.id),
        },
    )

    return ApproachConfirmationResponse(
        observation_id=observation.id,
        plate_number=observation.plate_number,
        confirmed_suspicion=payload.confirmed_suspicion,
        approach_outcome=payload.approach_outcome,
        notified_original_agent=True,
        original_agent_id=original_agent_id,
        original_agent_name=original_agent_name,
        feedback_event_id=feedback_event.id,
        processed_at=datetime.utcnow(),
    )


@router.post("/sync/batch", response_model=SyncBatchResponse)
async def sync_batch(
    payload: SyncBatchRequest,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    results: list[SyncResult] = []

    for item in payload.items:
        try:
            if item.entity_type != "observation":
                results.append(
                    SyncResult(
                        entity_local_id=item.entity_local_id,
                        status=SyncStatus.FAILED,
                        error=f"Tipo de entidade nao suportado: {item.entity_type}",
                    )
                )
                continue

            observation_payload = VehicleObservationCreate(**item.payload)
            existing_result = await db.execute(
                select(VehicleObservation).where(
                    VehicleObservation.client_id == observation_payload.client_id
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing is None:
                device = await get_or_register_device(
                    db,
                    device_identifier=observation_payload.device_id,
                    current_user=current_user,
                    app_version=payload.app_version,
                )
                synced = VehicleObservation(
                    client_id=observation_payload.client_id,
                    agent_id=current_user.id,
                    agency_id=current_user.agency_id,
                    device_id=device.id,
                    plate_number=observation_payload.plate_number,
                    plate_state=observation_payload.plate_state,
                    plate_country=observation_payload.plate_country,
                    observed_at_local=observation_payload.observed_at_local,
                    observed_at_server=datetime.utcnow(),
                    location=location_geometry(observation_payload.location),
                    location_accuracy=observation_payload.location.accuracy,
                    heading=observation_payload.heading,
                    speed=observation_payload.speed,
                    vehicle_color=observation_payload.vehicle_color,
                    vehicle_type=observation_payload.vehicle_type,
                    vehicle_model=observation_payload.vehicle_model,
                    vehicle_year=observation_payload.vehicle_year,
                    connectivity_type=observation_payload.connectivity_type,
                    sync_status=SyncStatus.COMPLETED,
                    sync_attempts=1,
                    synced_at=datetime.utcnow(),
                    metadata_snapshot={
                        "origin": "sync_batch",
                        "device_id": payload.device_id,
                        "app_version": payload.app_version,
                        "connectivity_type": observation_payload.connectivity_type or "unknown",
                        "payload_hash": item.payload_hash,
                    },
                )
                db.add(synced)
                await db.flush()

                if observation_payload.plate_read is not None:
                    db.add(
                        PlateRead(
                            observation_id=synced.id,
                            ocr_raw_text=observation_payload.plate_read.ocr_raw_text,
                            ocr_confidence=observation_payload.plate_read.ocr_confidence,
                            ocr_engine=observation_payload.plate_read.ocr_engine,
                            image_width=observation_payload.plate_read.image_width,
                            image_height=observation_payload.plate_read.image_height,
                            processing_time_ms=observation_payload.plate_read.processing_time_ms,
                        )
                    )
                    await db.flush()

                await evaluate_observation_algorithms(db, synced)
                operational_context = await build_operational_context_for_observation(
                    db,
                    observation=synced,
                )
                synced.metadata_snapshot = {
                    **(synced.metadata_snapshot or {}),
                    "state_registry_status": operational_context.get("state_registry"),
                    "prior_suspicion_context": operational_context.get("prior_suspicion"),
                }
                await event_bus.publish(
                    "observation_created",
                    {
                        "payload_version": "v1",
                        "observation_id": str(synced.id),
                        "agent_id": str(current_user.id),
                        "plate_number": synced.plate_number,
                        "source": "mobile_sync_batch",
                    },
                )
                server_id = synced.id
            else:
                server_id = existing.id

            results.append(
                SyncResult(
                    entity_local_id=item.entity_local_id,
                    entity_server_id=server_id,
                    status=SyncStatus.COMPLETED,
                    synced_at=datetime.utcnow(),
                )
            )
            await event_bus.publish(
                "sync_completed",
                {
                    "payload_version": "v1",
                    "entity_type": item.entity_type,
                    "entity_local_id": item.entity_local_id,
                    "entity_server_id": str(server_id),
                    "status": "completed",
                },
            )
        except Exception as exc:
            results.append(
                SyncResult(
                    entity_local_id=item.entity_local_id,
                    status=SyncStatus.FAILED,
                    error=str(exc),
                )
            )
            await event_bus.publish(
                "sync_completed",
                {
                    "payload_version": "v1",
                    "entity_type": item.entity_type,
                    "entity_local_id": item.entity_local_id,
                    "status": "failed",
                    "error": str(exc),
                },
            )

    success_count = sum(1 for result in results if result.status == SyncStatus.COMPLETED)
    failed_count = len(results) - success_count

    pending_feedback = [
        feedback.model_dump(mode="json")
        for feedback in (
            await fetch_pending_feedback_for_user(
                db,
                user=current_user,
                unread_only=True,
                limit=20,
            )
        )
    ]
    record_sync_batch(
        processed_count=len(payload.items),
        success_count=success_count,
        failed_count=failed_count,
    )
    record_feedback_pending(
        pending_count=len(pending_feedback),
        success=True,
    )

    return SyncBatchResponse(
        processed_count=len(payload.items),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
        server_timestamp=datetime.utcnow(),
        pending_feedback=pending_feedback,
    )


@router.post("/observations/{observation_id}/assets")
async def upload_observation_asset(
    observation_id: UUID,
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    observation = (
        await db.execute(
            select(VehicleObservation).where(
                and_(
                    VehicleObservation.id == observation_id,
                    VehicleObservation.agent_id == current_user.id,
                )
            )
        )
    ).scalars().first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada para upload de asset")

    asset_type_normalized = asset_type.strip().lower()
    if asset_type_normalized not in {"image", "audio"}:
        raise HTTPException(status_code=400, detail="asset_type invalido. Use 'image' ou 'audio'")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    uploaded = upload_observation_asset_bytes(
        observation_id=str(observation_id),
        asset_type=asset_type_normalized,
        original_filename=file.filename or f"{asset_type_normalized}.bin",
        content_type=file.content_type or "application/octet-stream",
        payload=payload,
    )

    asset = Asset(
        asset_type=asset_type_normalized,
        original_filename=file.filename or f"{asset_type_normalized}.bin",
        storage_key=uploaded.key,
        storage_bucket=uploaded.bucket,
        content_type=uploaded.content_type,
        size_bytes=uploaded.size_bytes,
        checksum_sha256=uploaded.checksum_sha256,
        uploaded_by=current_user.id,
        uploaded_from_device=observation.device_id,
        related_observation_id=observation.id,
    )
    db.add(asset)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="observation_asset_uploaded",
        resource_type="asset",
        resource_id=asset.id,
        details={
            "observation_id": str(observation_id),
            "asset_type": asset_type_normalized,
            "storage_key": uploaded.key,
            "size_bytes": uploaded.size_bytes,
        },
    )

    return {
        "asset_id": str(asset.id),
        "observation_id": str(observation_id),
        "asset_type": asset_type_normalized,
        "storage_bucket": uploaded.bucket,
        "storage_key": uploaded.key,
        "content_type": uploaded.content_type,
        "size_bytes": uploaded.size_bytes,
        "checksum_sha256": uploaded.checksum_sha256,
    }


@router.post("/observations/{observation_id}/assets/progressive")
async def upload_observation_asset_progressive(
    observation_id: UUID,
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    upload_id: Optional[str] = Form(None),
    chunk_index: int = Form(0),
    complete: bool = Form(False),
    parts: Optional[str] = Form(None),  # JSON string of parts
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    """
    Progressive upload endpoint for large assets.
    Supports chunked upload with retry capability.
    """
    observation = (
        await db.execute(
            select(VehicleObservation).where(
                and_(
                    VehicleObservation.id == observation_id,
                    VehicleObservation.agent_id == current_user.id,
                )
            )
        )
    ).scalars().first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada para upload de asset")

    asset_type_normalized = asset_type.strip().lower()
    if asset_type_normalized not in {"image", "audio"}:
        raise HTTPException(status_code=400, detail="asset_type invalido. Use 'image' ou 'audio'")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    # Handle progressive upload
    if complete and upload_id and parts:
        # Complete multipart upload
        import json
        parts_list = json.loads(parts)
        uploaded = complete_progressive_upload(
            upload_id=upload_id,
            key=f"observations/{observation_id}/{asset_type_normalized}/{file.filename or f'{asset_type_normalized}.bin'}",
            parts=parts_list,
        )
    else:
        # Upload chunk or initialize
        result = upload_observation_asset_progressive(
            observation_id=str(observation_id),
            asset_type=asset_type_normalized,
            original_filename=file.filename or f"{asset_type_normalized}.bin",
            content_type=file.content_type or "application/octet-stream",
            payload=payload,
            upload_id=upload_id,
            chunk_index=chunk_index,
        )
        
        if result["status"] == "completed":
            # Simple upload completed
            uploaded = UploadedAsset(
                bucket=result["asset"]["bucket"],
                key=result["asset"]["key"],
                content_type=file.content_type or "application/octet-stream",
                size_bytes=result["asset"]["size_bytes"],
                checksum_sha256=result["asset"]["checksum_sha256"],
            )
        else:
            # Return upload status for next chunk
            return result

    # Create asset record if upload completed
    asset = Asset(
        asset_type=asset_type_normalized,
        original_filename=file.filename or f"{asset_type_normalized}.bin",
        storage_key=uploaded.key,
        storage_bucket=uploaded.bucket,
        content_type=uploaded.content_type,
        size_bytes=uploaded.size_bytes,
        checksum_sha256=uploaded.checksum_sha256,
        uploaded_by=current_user.id,
        uploaded_from_device=observation.device_id,
        related_observation_id=observation.id,
    )
    db.add(asset)
    await db.flush()
    
    await log_audit_event(
        db,
        actor=current_user,
        action="observation_asset_uploaded",
        resource_type="asset",
        resource_id=asset.id,
        details={
            "observation_id": str(observation_id),
            "asset_type": asset_type_normalized,
            "storage_key": uploaded.key,
            "size_bytes": uploaded.size_bytes,
            "progressive": True,
        },
    )

    return {
        "asset_id": str(asset.id),
        "observation_id": str(observation_id),
        "asset_type": asset_type_normalized,
        "storage_bucket": uploaded.bucket,
        "storage_key": uploaded.key,
        "content_type": uploaded.content_type,
        "size_bytes": uploaded.size_bytes,
        "checksum_sha256": uploaded.checksum_sha256,
    }
