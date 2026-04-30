"""
F.A.R.O. Mobile API - fluxo do agente de campo.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
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
    AgentLocationLog,
    FeedbackEvent,
    IntelligenceReview,
    PlateRead,
    SuspicionReport,
    SyncStatus,
    SuspicionReason,
    SuspicionLevel,
    UrgencyLevel,
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
    OcrBatchValidationRequest,
    OcrBatchValidationResponse,
    PlateSuspicionCheckResponse,
    VehicleObservationCreate,
    VehicleObservationResponse,
)
from app.schemas.suspicion import SuspicionReportCreate, SuspicionReportResponse
from app.schemas.sync import SyncBatchRequest, SyncBatchResponse, SyncResult
from app.schemas.user import (
    AgentLocationBatchSync,
    AgentLocationUpdate,
    ShiftRenewalRequest,
)
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
from app.services.ocr_service import get_async_ocr_service
from app.services.storage_service import (
    UploadedAsset,
    complete_progressive_upload,
    upload_observation_asset_bytes,
    upload_observation_asset_progressive,
)
from app.services.ba_service import generate_ba_from_approach

logger = logging.getLogger(__name__)

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


@router.get("/")
async def mobile_root():
    """Mobile API root endpoint."""
    return {
        "module": "F.A.R.O. Mobile API",
        "version": "1.0.0",
        "description": "API para agentes de campo - observações, OCR, sincronização",
        "endpoints": [
            "/observations",
            "/history",
            "/plates/{plate_number}/check-suspicion",
            "/ocr/validate",
            "/ocr/batch",
            "/profile/current-location",
            "/profile/location-history",
            "/profile/duty/renew",
            "/sync/batch",
        ],
    }


@router.post("/observations", response_model=VehicleObservationResponse)
async def create_observation(
    payload: VehicleObservationCreate,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    try:
        if payload.client_id:
            existing_result = await db.execute(
                select(VehicleObservation).where(
                    VehicleObservation.client_id == payload.client_id
                )
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
        await db.commit()
        # Refresh observation to ensure all attributes are loaded for async operations
        await db.refresh(observation)
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
        # Refresh observation again before serialization to ensure all attributes are loaded
        await db.refresh(observation)
        return await serialize_observation(
            db,
            observation,
            current_user,
            operational_context=operational_context,
        )
    except Exception as e:
        import traceback
        logger.error(f"Error creating observation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating observation: {str(e)}"
        )


@router.get("/history", response_model=ObservationHistoryResponse)
async def get_observation_history(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.count(VehicleObservation.id)).where(
            VehicleObservation.agent_id == current_user.id
        )
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


@router.get("/observations/{observation_id}/feedback")
async def get_observation_feedback(
    observation_id: str,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    """Get feedback for an observation (compatibility endpoint)."""
    # Query feedback from intelligence review
    from sqlalchemy import select
    from app.db.base import IntelligenceReview, FeedbackEvent
    
    result = await db.execute(
        select(IntelligenceReview).where(
            IntelligenceReview.observation_id == observation_id
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        return {"feedback": None}
    
    # Get feedback event if exists
    feedback_result = await db.execute(
        select(FeedbackEvent).where(FeedbackEvent.review_id == review.id)
    )
    feedback = feedback_result.scalar_one_or_none()
    
    if feedback:
        return {
            "feedback": {
                "feedback_type": feedback.feedback_type,
                "title": feedback.title,
                "message": feedback.message,
                "recommended_action": feedback.recommended_action,
                "sent_at": feedback.sent_at.isoformat(),
                "read_at": feedback.read_at.isoformat() if feedback.read_at else None,
            }
        }
    
    return {"feedback": None}


@router.get(
    "/plates/{plate_number}/check-suspicion", response_model=PlateSuspicionCheckResponse
)
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
        ),
    )
    watchlist_entry = watchlist_result.scalar_one_or_none()

    # Determine if suspect
    is_suspect = watchlist_entry is not None or (
        prior_context and prior_context.get("has_prior_suspicion")
    )

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
        alert_title = (
            f"WATCHLIST: {watchlist_entry.category.value.replace('_', ' ').upper()}"
        )
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
        alert_parts.append(
            f"Categoria: {watchlist_category.replace('_', ' ').upper()}."
        )
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
        is_monitored=watchlist_entry is not None
        and watchlist_entry.category.value == "monitored_vehicle",
        intelligence_interest=prior_context is not None
        and prior_context.get("has_prior_suspicion"),
        has_active_watchlist=watchlist_entry is not None,
        watchlist_category=watchlist_category,
        guidance=guidance,
        requires_approach_confirmation=requires_approach,
        first_suspicion_agent_name=prior_context.get("first_suspicion_agent_name")
        if prior_context
        else None,
        first_suspicion_observation_id=UUID(
            prior_context["first_suspicion_observation_id"]
        )
        if prior_context and prior_context.get("first_suspicion_observation_id")
        else None,
        first_suspicion_at=prior_context.get("first_suspicion_at")
        if prior_context
        else None,
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
            detail=f"Invalid base64 image: {str(e)}",
        )

    # Get OCR service
    ocr_service = get_async_ocr_service()

    # Process image with backend OCR (async)
    result = await ocr_service.process_image_bytes_async(
        image_bytes=image_bytes, confidence_threshold=payload.confidence_threshold
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OCR processing failed - no plate detected",
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
            "match": payload.mobile_ocr_text.upper().replace(" ", "").replace("-", "")
            == result.plate_number,
        }

        # Consider improved if backend confidence is significantly higher
        if (
            payload.mobile_ocr_confidence
            and result.confidence > payload.mobile_ocr_confidence + 0.1
        ):
            improved_over_mobile = True

    return OcrValidationResponse(
        plate_number=result.plate_number,
        confidence=result.confidence,
        plate_format=result.plate_format,
        processing_time_ms=result.processing_time_ms,
        ocr_engine=result.ocr_engine,
        is_valid_format=is_valid,
        improved_over_mobile=improved_over_mobile,
        mobile_comparison=mobile_comparison,
    )


@router.post("/ocr/batch", response_model=OcrBatchValidationResponse)
async def validate_ocr_batch(
    payload: OcrBatchValidationRequest,
    current_user: User = Depends(require_field_agent),
):
    """
    Process multiple images in parallel using backend YOLOv11 + EasyOCR.
    
    Batch processing for improved throughput when multiple images need OCR.
    """
    import base64
    from io import BytesIO
    
    # Get OCR service
    ocr_service = get_async_ocr_service()
    
    # Decode all images
    image_bytes_list = []
    for img_b64 in payload.images_base64:
        try:
            image_bytes_list.append(base64.b64decode(img_b64))
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
    
    # Process in batch parallel
    results_data = await ocr_service.process_batch_async(
        image_bytes_list,
        confidence_threshold=payload.confidence_threshold
    )
    
    # Build response
    results = []
    successful = 0
    failed = 0
    
    for result in results_data:
        if result:
            is_valid, plate_format = ocr_service.validate_plate_number(result.plate_number)
            results.append(OcrValidationResponse(
                plate_number=result.plate_number,
                confidence=result.confidence,
                plate_format=result.plate_format,
                processing_time_ms=result.processing_time_ms,
                ocr_engine=result.ocr_engine,
                is_valid_format=is_valid,
            ))
            successful += 1
        else:
            failed += 1
    
    return OcrBatchValidationResponse(
        results=results,
        total_processed=len(image_bytes_list),
        successful=successful,
        failed=failed,
    )


@router.post(
    "/observations/{observation_id}/suspicion", response_model=SuspicionReportResponse
)
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
        raise HTTPException(
            status_code=400, detail="Observacao ja possui suspeicao registrada"
        )

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


@router.get(
    "/observations/{observation_id}/feedback", response_model=list[FeedbackForAgent]
)
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

    merged_feedback.extend(
        [
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
        ]
    )
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

    # Get or create SuspicionReport for this observation to store approach data
    report_result = await db.execute(
        select(SuspicionReport).where(SuspicionReport.observation_id == observation_id)
    )
    report = report_result.scalar_one_or_none()

    if report is None:
        report = SuspicionReport(
            observation_id=observation_id,
            reason=SuspicionReason.OTHER,
            level=SuspicionLevel.LOW,
            urgency=UrgencyLevel.MONITOR,
            notes="Abordagem registrada",
        )
        db.add(report)
        await db.flush()

    # Persist tactical approach data
    report.abordado = payload.was_approached
    report.nivel_abordagem = payload.suspicion_level_slider
    report.ocorrencia_registrada = payload.has_incident
    report.street_direction = payload.street_direction

    if payload.notes:
        report.notes = (
            f"{report.notes}\n\n[NOTAS DE CAMPO]: {payload.notes}"
            if report.notes
            else f"[NOTAS DE CAMPO]: {payload.notes}"
        )
    await db.flush()

    # Busca suspeita de QUALQUER agencia (para encontrar o cadastrador original)
    prior_context = await get_first_prior_suspicion_for_plate(
        db,
        plate_number=observation.plate_number,
        agency_id=None,
        exclude_observation_id=observation.id,
    )

    common_details = {
        "confirmed_suspicion": payload.confirmed_suspicion,
        "approach_outcome": payload.approach_outcome,
        "suspicion_level_slider": payload.suspicion_level_slider,
        "was_approached": payload.was_approached,
        "has_incident": payload.has_incident,
        "street_direction": payload.street_direction.value
        if payload.street_direction
        else None,
    }

    if not prior_context or not prior_context.get("has_prior_suspicion"):
        await log_audit_event(
            db,
            actor=current_user,
            action="approach_confirmation_recorded",
            resource_type="vehicle_observation",
            resource_id=observation.id,
            details={**common_details, "notified_original_agent": False},
            justification=payload.notes,
        )
        await event_bus.publish(
            "field_approach_confirmed",
            {
                "payload_version": "v1",
                "observation_id": str(observation.id),
                "plate_number": observation.plate_number,
                **common_details,
                "notified_original_agent": False,
            },
        )

        # ── Gera Boletim de Atendimento (BA) ──
        try:
            await generate_ba_from_approach(
                db,
                observation_id=observation.id,
                approach_data=common_details
                | {
                    "notes": payload.notes,
                    "approached_at_local": payload.approached_at_local,
                },
                current_user=current_user,
            )
        except Exception as ba_err:
            logger.warning("Falha ao gerar BA para obs %s: %s", observation.id, ba_err)

        return ApproachConfirmationResponse(
            observation_id=observation.id,
            plate_number=observation.plate_number,
            confirmed_suspicion=payload.confirmed_suspicion,
            approach_outcome=payload.approach_outcome,
            notified_original_agent=False,
            processed_at=datetime.utcnow(),
        )

    original_agent_id = UUID(prior_context["first_suspicion_agent_id"])
    original_agency_id = UUID(prior_context["first_suspicion_agency_id"])
    original_agent_name = prior_context.get("first_suspicion_agent_name")
    observation_point = to_shape(observation.location)
    location_hint = (
        f"{payload.location.latitude:.6f}, {payload.location.longitude:.6f}"
        if payload.location is not None
        else f"{observation_point.y:.6f}, {observation_point.x:.6f}"
    )
    confirmation_label = (
        "confirmada" if payload.confirmed_suspicion else "nao confirmada"
    )
    direction_label = (
        f" (Sentido: {payload.street_direction.value})"
        if payload.street_direction
        else ""
    )

    message = (
        f"Abordagem registrada para placa {observation.plate_number}. "
        f"Suspeicao {confirmation_label}{direction_label}. "
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

    feedback_event = AnalystFeedbackEvent(
        agency_id=original_agency_id,
        observation_id=UUID(prior_context["first_suspicion_observation_id"]),
        analyst_id=current_user.id,
        target_user_id=original_agent_id,
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
            **common_details,
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
            **common_details,
            "original_agent_id": str(original_agent_id),
            "feedback_event_id": str(feedback_event.id),
        },
    )

    try:
        await generate_ba_from_approach(
            db,
            observation_id=observation.id,
            approach_data=common_details
            | {
                "notes": payload.notes,
                "approached_at_local": payload.approached_at_local,
            },
            current_user=current_user,
        )
    except Exception as ba_err:
        logger.warning("Falha ao gerar BA para obs %s: %s", observation.id, ba_err)

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


@router.post("/profile/current-location")
async def update_current_location(
    payload: AgentLocationUpdate,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the agent's current live location for tactical routing.
    This is high-frequency and only updates the current state.
    """
    current_user.last_known_location = location_geometry(payload.location)
    current_user.last_seen = datetime.utcnow()

    # Also log to history for audit trail
    log = AgentLocationLog(
        agent_id=current_user.id,
        location=location_geometry(payload.location),
        recorded_at=payload.recorded_at,
        connectivity_status=payload.connectivity_status,
        battery_level=payload.battery_level,
    )
    db.add(log)

    await db.commit()
    return {
        "message": "Current location updated",
        "status": "success",
        "on_duty": current_user.is_on_duty,
    }


@router.post("/profile/location-history")
async def sync_location_history(
    payload: AgentLocationBatchSync,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    for item in payload.items:
        log = AgentLocationLog(
            agent_id=current_user.id,
            location=location_geometry(item.location),
            recorded_at=item.recorded_at,
            connectivity_status=item.connectivity_status,
            battery_level=item.battery_level,
        )
        db.add(log)

    await db.commit()
    return {
        "message": f"Sincronizado com sucesso {len(payload.items)} historical locations",
        "status": "synced",
        "count": len(payload.items),
    }


@router.post("/profile/duty/renew")
async def renew_duty_shift(
    payload: ShiftRenewalRequest,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    expires_at = datetime.utcnow() + timedelta(hours=payload.shift_duration_hours)
    current_user.is_on_duty = True
    current_user.service_expires_at = expires_at

    await log_audit_event(
        db,
        actor=current_user,
        action="duty_renewed",
        resource_type="user_profile",
        resource_id=current_user.id,
        details={
            "shift_duration_hours": payload.shift_duration_hours,
            "expires_at": expires_at.isoformat(),
        },
    )
    await db.commit()

    return {
        "message": f"Turno renovado com sucesso por +{payload.shift_duration_hours}h"
    }


@router.post("/observations/{observation_id}/approach-confirmation")
async def submit_approach_confirmation(
    observation_id: str,
    payload: dict,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    """Submit approach confirmation for an observation (compatibility endpoint)."""
    # Update or create suspicion report with approach details
    from sqlalchemy import select
    from app.db.base import VehicleObservation, SuspicionReport, SuspicionLevel, UrgencyLevel
    from datetime import datetime
    
    result = await db.execute(
        select(VehicleObservation).where(VehicleObservation.id == observation_id)
    )
    observation = result.scalar_one_or_none()
    
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    # Check if the observation belongs to the current user
    if observation.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your observation")
    
    # Update or create suspicion report with approach confirmation
    suspicion_result = await db.execute(
        select(SuspicionReport).where(SuspicionReport.observation_id == observation_id)
    )
    suspicion = suspicion_result.scalar_one_or_none()
    
    if suspicion:
        # Update existing suspicion report with approach confirmation
        suspicion.abordado = payload.get("abordado", True)
        suspicion.nivel_abordagem = payload.get("nivel_abordagem")
        suspicion.ocorrencia_registrada = payload.get("ocorrencia_registrada", False)
        suspicion.texto_ocorrencia = payload.get("texto_ocorrencia")
        suspicion.street_direction = payload.get("street_direction")
        suspicion.approach_confirmed_at = datetime.utcnow()
        
        # Update urgency if provided
        if payload.get("urgency"):
            suspicion.urgency = UrgencyLevel[payload["urgency"].upper()]
        
        await db.commit()
    else:
        # Create new suspicion report with approach confirmation
        new_suspicion = SuspicionReport(
            observation_id=observation_id,
            reason=payload.get("reason", "APPROACH_CONFIRMATION"),
            level=SuspicionLevel[payload.get("level", "MEDIUM").upper()],
            urgency=UrgencyLevel[payload.get("urgency", "APPROACH").upper()],
            abordado=payload.get("abordado", True),
            nivel_abordagem=payload.get("nivel_abordagem"),
            ocorrencia_registrada=payload.get("ocorrencia_registrada", False),
            texto_ocorrencia=payload.get("texto_ocorrencia"),
            street_direction=payload.get("street_direction"),
            approach_confirmed_at=datetime.utcnow(),
        )
        db.add(new_suspicion)
        await db.commit()
    
    return {
        "message": "Approach confirmation submitted successfully",
        "observation_id": observation_id,
        "approach_confirmed": True
    }


@router.post("/sync/batch", response_model=SyncBatchResponse)
async def sync_batch(
    payload: SyncBatchRequest,
    current_user: User = Depends(require_field_agent),
    db: AsyncSession = Depends(get_db),
):
    # Apply circuit breaker for sync endpoint
    from app.core.circuit_breaker import get_endpoint_circuit_breaker, CircuitState
    from app.utils.adaptive_insertion import AdaptiveInsertionStrategy
    
    sync_cb = get_endpoint_circuit_breaker("mobile_sync")
    if not sync_cb.can_execute():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=f"Circuit breaker OPEN - sync temporariamente indisponível. Tente novamente em {sync_cb.config.timeout_seconds}s"
        )
    
    # Initialize adaptive insertion strategy
    adaptive_strategy = AdaptiveInsertionStrategy(
        initial_batch_size=50,
        max_batch_size=200,
        min_batch_size=10
    )
    
    results: list[SyncResult] = []
    
    try:
        # Adapt insertion mode based on current conditions
        await adaptive_strategy.adapt_mode(db)
        
        # Process items in batches based on adaptive strategy
        items_to_process = payload.items
        batch_start = 0
        
        while batch_start < len(items_to_process):
            batch_end = min(batch_start + adaptive_strategy.batch_size, len(items_to_process))
            batch_items = items_to_process[batch_start:batch_end]
            
            batch_start_time = time.time()
            batch_success = 0
            batch_failed = 0
            
            for item in batch_items:
                try:
                    if item.entity_type != "observation":
                        results.append(SyncResult(
                            entity_local_id=item.entity_local_id,
                            status=SyncStatus.FAILED,
                            error=f"Tipo de entidade nao suportado: {item.entity_type}",
                        ))
                        batch_failed += 1
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
                                "connectivity_type": observation_payload.connectivity_type
                                or "unknown",
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
                            "prior_suspicion_context": operational_context.get(
                                "prior_suspicion"
                            ),
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
                    batch_success += 1
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
                    batch_failed += 1
            
            # Commit batch
            await db.commit()
            
            # Update adaptive metrics
            batch_latency = time.time() - batch_start_time
            batch_success_rate = batch_success / len(batch_items) if batch_items else 0
            adaptive_strategy.update_metrics(
                success=batch_success_rate > 0.9,
                latency=batch_latency
            )
            
            # Move to next batch
            batch_start = batch_end
            
            # Re-adapt mode for next batch
            await adaptive_strategy.adapt_mode(db)

    except Exception as e:
        # Record failure in circuit breaker
        sync_cb.record_failure(500)
        await db.rollback()
        raise
    
    # Record success in circuit breaker
    sync_cb.record_success()
    
    success_count = sum(
        1 for result in results if result.status == SyncStatus.COMPLETED
    )
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
        (
            await db.execute(
                select(VehicleObservation).where(
                    and_(
                        VehicleObservation.id == observation_id,
                        VehicleObservation.agent_id == current_user.id,
                    )
                )
            )
        )
        .scalars()
        .first()
    )
    if observation is None:
        raise HTTPException(
            status_code=404, detail="Observacao nao encontrada para upload de asset"
        )

    asset_type_normalized = asset_type.strip().lower()
    if asset_type_normalized not in {"image", "audio"}:
        raise HTTPException(
            status_code=400, detail="asset_type invalido. Use 'image' ou 'audio'"
        )

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
        (
            await db.execute(
                select(VehicleObservation).where(
                    and_(
                        VehicleObservation.id == observation_id,
                        VehicleObservation.agent_id == current_user.id,
                    )
                )
            )
        )
        .scalars()
        .first()
    )
    if observation is None:
        raise HTTPException(
            status_code=404, detail="Observacao nao encontrada para upload de asset"
        )

    asset_type_normalized = asset_type.strip().lower()
    if asset_type_normalized not in {"image", "audio"}:
        raise HTTPException(
            status_code=400, detail="asset_type invalido. Use 'image' ou 'audio'"
        )

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
