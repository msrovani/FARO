"""
F.A.R.O. Intelligence API - triagem, analise estruturada e retorno ao campo.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, case, desc, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.core.config import settings
from app.core.observability import (
    record_feedback_pending,
    record_feedback_read,
    record_feedback_sent,
    record_queue_fetch,
)
from app.db.base import (
    AnalystFeedbackEvent,
    AnalystFeedbackTemplate,
    AnalystReview,
    AnalystReviewVersion,
    FeedbackEvent,
    ImpossibleTravelEvent,
    IntelligenceCase,
    IntelligenceReview,
    PlateRead,
    RoamingEvent,
    RouteAnomalyEvent,
    RoutePattern,
    SensitiveAssetRecurrenceEvent,
    SuspicionReport,
    SuspicionScore,
    SuspicionScoreFactor,
    SuspiciousRoute,
    Unit,
    User,
    UserRole,
    VehicleObservation,
    WatchlistEntry,
    WatchlistHit,
    WatchlistStatus,
    ConvoyEvent,
    CaseStatus,
    CaseLink,
    Agency,
)
from app.schemas.analytics import (
    AlgorithmResultResponse,
    AnalystFeedbackCreateRequest,
    AnalystFeedbackResponse,
    AnalystFeedbackTemplateCreateRequest,
    AnalystFeedbackTemplateResponse,
    FeedbackRecipientResponse,
    AnalystReviewCreateRequest,
    AnalystReviewResponse,
    AnalystReviewUpdateRequest,
    IntelligenceCaseCreate,
    IntelligenceCaseResponse,
    IntelligenceCaseUpdate,
    CaseLinkCreate,
    CaseLinkResponse,
    ObservationAnalyticDetailResponse,
    SuspicionScoreFactorResponse,
    SuspicionScoreResponse,
    QueueScoreSummary,
)
from app.schemas.agency import (
    AgencyResponse,
    AgencyListResponse,
)
from app.schemas.common import GeolocationPoint, PaginationParams
from app.schemas.intelligence import (
    FeedbackForAgent,
    IntelligenceQueueFilter,
    IntelligenceQueueItem,
    MarkFeedbackReadRequest,
)
from app.schemas.watchlist import (
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    WatchlistEntryUpdate,
)
from app.schemas.route import (
    RouteAnalysisRequest,
    RoutePatternResponse,
    RouteTimelineResponse,
)
from app.schemas.suspicious_route import (
    SuspiciousRouteCreate,
    SuspiciousRouteUpdate,
    SuspiciousRouteResponse,
    SuspiciousRouteMatchRequest,
    SuspiciousRouteMatchResponse,
    SuspiciousRouteListResponse,
    RouteApprovalRequest,
)
from app.services.audit_service import log_audit_event
from app.services.event_bus import event_bus
from app.services.feedback_service import fetch_pending_feedback_for_user
from app.services.websocket_service import websocket_manager
from app.services.observation_service import fetch_plate_activity_map, serialize_observation
from app.services.route_analysis_service import analyze_vehicle_route, get_route_timeline, save_route_pattern
from app.services.suspicious_route_service import (
    create_suspicious_route,
    get_suspicious_route,
    list_suspicious_routes,
    update_suspicious_route,
    delete_suspicious_route,
    check_route_match,
    approve_route,
    route_to_response,
)

router = APIRouter()


def require_intelligence_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de inteligencia requerido")
    if current_user.role != UserRole.ADMIN and current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    return current_user


def require_field_capable_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {
        UserRole.FIELD_AGENT,
        UserRole.INTELLIGENCE,
        UserRole.SUPERVISOR,
        UserRole.ADMIN,
    }:
        raise HTTPException(status_code=403, detail="Usuario sem acesso operacional")
    return current_user


def scoped_query(query, current_user: User, column):
    """Filter query by agency based on user role and agency hierarchy."""
    if current_user.role == UserRole.ADMIN:
        return query
    
    # Get user's agency
    from sqlalchemy import select
    from app.db.base import Agency, AgencyType
    
    # Simple agency filter for now - can be extended with hierarchy
    return query.where(column == current_user.agency_id)


def get_agency_scope_filter(current_user: User, column):
    """
    Get agency filter based on user's agency type and hierarchy.
    
    Returns a filter condition for queries based on:
    - LOCAL: Sees only their own agency
    - REGIONAL: Sees their agency + child local agencies
    - CENTRAL: Sees all agencies (like ADMIN)
    """
    from sqlalchemy import or_
    from app.db.base import Agency, AgencyType
    
    if current_user.role == UserRole.ADMIN:
        return True  # No filter
    
    # For now, return simple agency filter
    # TODO: Implement hierarchy-based filtering with child agencies
    # This requires loading the user's agency and its type, then filtering accordingly
    return column == current_user.agency_id


async def get_user_agency_with_hierarchy(current_user: User, db: AsyncSession) -> Agency | None:
    """Load user's agency with hierarchy information."""
    from app.db.base import Agency
    
    result = await db.execute(
        select(Agency).where(Agency.id == current_user.agency_id)
    )
    return result.scalar_one_or_none()


async def get_child_agency_ids(parent_agency_id: str, db: AsyncSession) -> list[str]:
    """Get all child agency IDs for a parent agency."""
    from app.db.base import Agency
    
    result = await db.execute(
        select(Agency.id).where(Agency.parent_agency_id == parent_agency_id)
    )
    return [row[0] for row in result.all()]


def serialize_watchlist_entry(entry: WatchlistEntry, creator_name: str | None) -> WatchlistEntryResponse:
    return WatchlistEntryResponse(
        id=entry.id,
        created_by=entry.created_by,
        created_by_name=creator_name,
        status=entry.status,
        category=entry.category,
        plate_number=entry.plate_number,
        plate_partial=entry.plate_partial,
        vehicle_make=entry.vehicle_make,
        vehicle_model=entry.vehicle_model,
        vehicle_color=entry.vehicle_color,
        visual_traits=entry.visual_traits,
        interest_reason=entry.interest_reason,
        information_source=entry.information_source,
        sensitivity_level=entry.sensitivity_level,
        confidence_level=entry.confidence_level,
        geographic_scope=entry.geographic_scope,
        active_time_window=entry.active_time_window,
        priority=entry.priority,
        recommended_action=entry.recommended_action,
        silent_mode=entry.silent_mode,
        notes=entry.notes,
        valid_from=entry.valid_from,
        valid_until=entry.valid_until,
        review_due_at=entry.review_due_at,
        metadata_json=entry.metadata_json,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def serialize_case(case_row: IntelligenceCase, creator_name: str | None) -> IntelligenceCaseResponse:
    return IntelligenceCaseResponse(
        id=case_row.id,
        title=case_row.title,
        hypothesis=case_row.hypothesis,
        summary=case_row.summary,
        status=case_row.status,
        sensitivity_level=case_row.sensitivity_level,
        priority=case_row.priority,
        review_due_at=case_row.review_due_at,
        created_by=case_row.created_by,
        created_by_name=creator_name,
        created_at=case_row.created_at,
        updated_at=case_row.updated_at,
    )


def serialize_case_link(link: CaseLink, creator_name: str | None) -> CaseLinkResponse:
    return CaseLinkResponse(
        id=link.id,
        case_id=link.case_id,
        link_type=link.link_type,
        linked_entity_id=link.linked_entity_id,
        linked_label=link.linked_label,
        created_by=link.created_by,
        created_by_name=creator_name,
        created_at=link.created_at,
    )


def serialize_analyst_review(review: AnalystReview, analyst_name: str | None) -> AnalystReviewResponse:
    return AnalystReviewResponse(
        id=review.id,
        observation_id=review.observation_id,
        analyst_id=review.analyst_id,
        analyst_name=analyst_name,
        status=review.status,
        conclusion=review.conclusion,
        decision=review.decision,
        source_quality=review.source_quality,
        data_reliability=review.data_reliability,
        reinforcing_factors=review.reinforcing_factors,
        weakening_factors=review.weakening_factors,
        recommendation=review.recommendation,
        justification=review.justification,
        sensitivity_level=review.sensitivity_level,
        review_due_at=review.review_due_at,
        linked_case_id=review.linked_case_id,
        linked_occurrence_ref=review.linked_occurrence_ref,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def serialize_analyst_feedback(
    feedback: AnalystFeedbackEvent,
    analyst_name: str | None,
) -> AnalystFeedbackResponse:
    return AnalystFeedbackResponse(
        id=feedback.id,
        observation_id=feedback.observation_id,
        analyst_id=feedback.analyst_id,
        analyst_name=analyst_name,
        target_user_id=feedback.target_user_id,
        target_team_label=feedback.target_team_label,
        feedback_type=feedback.feedback_type,
        sensitivity_level=feedback.sensitivity_level,
        title=feedback.title,
        message=feedback.message,
        delivered_at=feedback.delivered_at,
        read_at=feedback.read_at,
        created_at=feedback.created_at,
    )


def serialize_feedback_template(
    template: AnalystFeedbackTemplate,
    creator_name: str | None,
) -> AnalystFeedbackTemplateResponse:
    return AnalystFeedbackTemplateResponse(
        id=template.id,
        created_by=template.created_by,
        created_by_name=creator_name,
        name=template.name,
        feedback_type=template.feedback_type,
        sensitivity_level=template.sensitivity_level,
        body_template=template.body_template,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def serialize_score(
    score_row: SuspicionScore,
    factors: list[SuspicionScoreFactor],
) -> SuspicionScoreResponse:
    return SuspicionScoreResponse(
        id=score_row.id,
        observation_id=score_row.observation_id,
        plate_number=score_row.plate_number,
        final_score=score_row.final_score,
        final_label=score_row.final_label,
        confidence=score_row.confidence,
        severity=score_row.severity,
        explanation=score_row.explanation,
        false_positive_risk=score_row.false_positive_risk,
        factors=[
            SuspicionScoreFactorResponse(
                factor_name=factor.factor_name,
                factor_source=factor.factor_source,
                weight=factor.weight,
                contribution=factor.contribution,
                explanation=factor.explanation,
                direction=factor.direction,
            )
            for factor in factors
        ],
        created_at=score_row.created_at,
    )


def serialize_algorithm_result(
    *,
    event_id,
    algorithm_type,
    observation_id,
    plate_number,
    decision,
    confidence,
    severity,
    explanation,
    false_positive_risk,
    metrics,
    created_at,
) -> AlgorithmResultResponse:
    return AlgorithmResultResponse(
        id=event_id,
        algorithm_type=algorithm_type,
        observation_id=observation_id,
        plate_number=plate_number,
        decision=decision,
        confidence=confidence,
        severity=severity,
        explanation=explanation,
        false_positive_risk=false_positive_risk,
        metrics=metrics,
        created_at=created_at,
    )


async def build_algorithm_results_for_observation(
    db: AsyncSession,
    observation_id: UUID,
) -> list[AlgorithmResultResponse]:
    results: list[AlgorithmResultResponse] = []

    watchlist_hits = (
        await db.execute(select(WatchlistHit).where(WatchlistHit.observation_id == observation_id))
    ).scalars().all()
    for hit in watchlist_hits:
        results.append(
            serialize_algorithm_result(
                event_id=hit.id,
                algorithm_type="watchlist",
                observation_id=hit.observation_id,
                plate_number=None,
                decision=hit.decision,
                confidence=hit.confidence,
                severity=hit.severity,
                explanation=hit.explanation,
                false_positive_risk=hit.false_positive_risk,
                metrics={"watchlist_entry_id": str(hit.watchlist_entry_id)},
                created_at=hit.created_at,
            )
        )

    impossible_events = (
        await db.execute(
            select(ImpossibleTravelEvent).where(ImpossibleTravelEvent.observation_id == observation_id)
        )
    ).scalars().all()
    for event in impossible_events:
        results.append(
            serialize_algorithm_result(
                event_id=event.id,
                algorithm_type="impossible_travel",
                observation_id=event.observation_id,
                plate_number=event.plate_number,
                decision=event.decision,
                confidence=event.confidence,
                severity=event.severity,
                explanation=event.explanation,
                false_positive_risk=event.false_positive_risk,
                metrics={
                    "distance_km": event.distance_km,
                    "travel_time_minutes": event.travel_time_minutes,
                    "plausible_time_minutes": event.plausible_time_minutes,
                    "previous_observation_id": str(event.previous_observation_id)
                    if event.previous_observation_id
                    else None,
                },
                created_at=event.created_at,
            )
        )

    route_events = (
        await db.execute(select(RouteAnomalyEvent).where(RouteAnomalyEvent.observation_id == observation_id))
    ).scalars().all()
    for event in route_events:
        results.append(
            serialize_algorithm_result(
                event_id=event.id,
                algorithm_type="route_anomaly",
                observation_id=event.observation_id,
                plate_number=event.plate_number,
                decision=event.decision,
                confidence=event.confidence,
                severity=event.severity,
                explanation=event.explanation,
                false_positive_risk=event.false_positive_risk,
                metrics={
                    "region_from_id": str(event.region_from_id) if event.region_from_id else None,
                    "region_to_id": str(event.region_to_id) if event.region_to_id else None,
                    "anomaly_score": event.anomaly_score,
                },
                created_at=event.created_at,
            )
        )

    sensitive_events = (
        await db.execute(
            select(SensitiveAssetRecurrenceEvent).where(
                SensitiveAssetRecurrenceEvent.observation_id == observation_id
            )
        )
    ).scalars().all()
    for event in sensitive_events:
        results.append(
            serialize_algorithm_result(
                event_id=event.id,
                algorithm_type="sensitive_zone_recurrence",
                observation_id=event.observation_id,
                plate_number=event.plate_number,
                decision=event.decision,
                confidence=event.confidence,
                severity=event.severity,
                explanation=event.explanation,
                false_positive_risk=event.false_positive_risk,
                metrics={"zone_id": str(event.zone_id), "recurrence_count": event.recurrence_count},
                created_at=event.created_at,
            )
        )

    convoy_events = (
        await db.execute(select(ConvoyEvent).where(ConvoyEvent.observation_id == observation_id))
    ).scalars().all()
    for event in convoy_events:
        results.append(
            serialize_algorithm_result(
                event_id=event.id,
                algorithm_type="convoy",
                observation_id=event.observation_id,
                plate_number=event.primary_plate,
                decision=event.decision,
                confidence=event.confidence,
                severity=event.severity,
                explanation=event.explanation,
                false_positive_risk=event.false_positive_risk,
                metrics={
                    "related_plate": event.related_plate,
                    "cooccurrence_count": event.cooccurrence_count,
                },
                created_at=event.created_at,
            )
        )

    roaming_events = (
        await db.execute(select(RoamingEvent).where(RoamingEvent.observation_id == observation_id))
    ).scalars().all()
    for event in roaming_events:
        results.append(
            serialize_algorithm_result(
                event_id=event.id,
                algorithm_type="roaming",
                observation_id=event.observation_id,
                plate_number=event.plate_number,
                decision=event.decision,
                confidence=event.confidence,
                severity=event.severity,
                explanation=event.explanation,
                false_positive_risk=event.false_positive_risk,
                metrics={"area_label": event.area_label, "recurrence_count": event.recurrence_count},
                created_at=event.created_at,
            )
        )

    return sorted(results, key=lambda item: item.created_at, reverse=True)


async def create_review_version(
    db: AsyncSession,
    review: AnalystReview,
    *,
    changed_by: UUID,
    change_reason: str | None,
) -> AnalystReviewVersion:
    last_version_number = (
        await db.execute(
            select(func.max(AnalystReviewVersion.version_number)).where(
                AnalystReviewVersion.analyst_review_id == review.id
            )
        )
    ).scalar()
    snapshot = {
        "status": review.status.value,
        "conclusion": review.conclusion.value if review.conclusion else None,
        "decision": review.decision.value if review.decision else None,
        "source_quality": review.source_quality,
        "data_reliability": review.data_reliability,
        "reinforcing_factors": review.reinforcing_factors,
        "weakening_factors": review.weakening_factors,
        "recommendation": review.recommendation,
        "justification": review.justification,
        "sensitivity_level": review.sensitivity_level,
        "review_due_at": review.review_due_at.isoformat() if review.review_due_at else None,
        "linked_case_id": str(review.linked_case_id) if review.linked_case_id else None,
        "linked_occurrence_ref": review.linked_occurrence_ref,
    }
    version = AnalystReviewVersion(
        analyst_review_id=review.id,
        version_number=(last_version_number or 0) + 1,
        changed_by=changed_by,
        change_reason=change_reason,
        snapshot_json=snapshot,
    )
    db.add(version)
    await db.flush()
    return version


@router.get("/queue", response_model=list[IntelligenceQueueItem])
async def get_intelligence_queue(
    filters: IntelligenceQueueFilter = Depends(),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(VehicleObservation, SuspicionReport, User, Unit)
        .join(SuspicionReport, SuspicionReport.observation_id == VehicleObservation.id)
        .join(User, User.id == VehicleObservation.agent_id)
        .outerjoin(Unit, Unit.id == User.unit_id)
        .outerjoin(AnalystReview, AnalystReview.observation_id == VehicleObservation.id)
        .where(or_(AnalystReview.id.is_(None), AnalystReview.status != "final"))
    )
    query = scoped_query(query, current_user, VehicleObservation.agency_id)

    if filters.plate_number:
        query = query.where(VehicleObservation.plate_number.ilike(f"%{filters.plate_number}%"))
    if filters.suspicion_level:
        query = query.where(SuspicionReport.level == filters.suspicion_level)
    if filters.urgency:
        query = query.where(SuspicionReport.urgency == filters.urgency)
    if filters.reason:
        query = query.where(SuspicionReport.reason == filters.reason)
    if filters.agent_id:
        query = query.where(VehicleObservation.agent_id == filters.agent_id)
    if filters.unit_id:
        query = query.where(User.unit_id == filters.unit_id)
    if filters.date_from:
        query = query.where(VehicleObservation.observed_at_local >= filters.date_from)
    if filters.date_to:
        query = query.where(VehicleObservation.observed_at_local <= filters.date_to)

    # Apply automatic prioritization if enabled
    if settings.queue_auto_prioritization_enabled:
        # Use composite score: score_weight * suspicion_score + urgency_weight * urgency_rank
        query = (
            query.outerjoin(SuspicionScore, SuspicionScore.observation_id == VehicleObservation.id)
            .order_by(
                case(
                    (SuspicionReport.urgency == "approach", 1),
                    (SuspicionReport.urgency == "intelligence", 2),
                    (SuspicionReport.urgency == "monitor", 3),
                    else_=4,
                ).label("urgency_rank"),
                (SuspicionScore.final_score * settings.queue_score_weight).desc(nulls_last=True),
                VehicleObservation.observed_at_local.desc(),
            )
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    else:
        # Fallback to FIFO manual ordering by urgency and time
        query = (
            query.order_by(
                case(
                    (SuspicionReport.urgency == "approach", 1),
                    (SuspicionReport.urgency == "intelligence", 2),
                    (SuspicionReport.urgency == "monitor", 3),
                    else_=4,
                ),
                VehicleObservation.observed_at_local.desc(),
            )
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

    rows = (await db.execute(query)).all()
    observation_ids = [observation.id for observation, _, _, _ in rows]
    plate_numbers = [observation.plate_number for observation, _, _, _ in rows]

    activity_map = await fetch_plate_activity_map(db, plate_numbers, agency_id=current_user.agency_id)
    score_rows = (
        await db.execute(select(SuspicionScore).where(SuspicionScore.observation_id.in_(observation_ids)))
    ).scalars().all() if observation_ids else []
    score_map = {score.observation_id: score for score in score_rows}

    items: list[IntelligenceQueueItem] = []
    for observation, suspicion, agent, unit in rows:
        point = to_shape(observation.location)
        activity = activity_map.get(
            observation.plate_number,
            {"completed_count": 0, "is_monitored": False},
        )
        score = score_map.get(observation.id)
        items.append(
            IntelligenceQueueItem(
                observation_id=observation.id,
                plate_number=observation.plate_number,
                observed_at=observation.observed_at_local,
                location=GeolocationPoint(latitude=point.y, longitude=point.x),
                agent_name=agent.full_name,
                unit_name=unit.name if unit else None,
                suspicion_reason=suspicion.reason,
                suspicion_level=suspicion.level,
                urgency=suspicion.urgency,
                suspicion_notes=suspicion.notes,
                previous_observations_count=max(int(activity["completed_count"]) - 1, 0),
                is_monitored=bool(activity["is_monitored"]),
                has_image=suspicion.image_url is not None,
                score_value=score.final_score if score else None,
                score_label=score.final_label.value if score else None,
                priority_source=score.explanation if score else "priorizacao por suspeicao do campo",
                added_to_queue_at=observation.created_at,
            )
        )
    record_queue_fetch(items_count=len(items), success=True)
    return items


@router.get("/observations/{observation_id}", response_model=ObservationAnalyticDetailResponse)
async def get_observation_detail(
    observation_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VehicleObservation, User)
        .join(User, User.id == VehicleObservation.agent_id)
        .where(VehicleObservation.id == observation_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")

    observation, agent = row
    if current_user.role != UserRole.ADMIN and observation.agency_id != current_user.agency_id:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")
    base_response = await serialize_observation(db, observation, agent)
    algorithm_results = await build_algorithm_results_for_observation(db, observation_id)

    suspicion_report_row = (
        await db.execute(select(SuspicionReport).where(SuspicionReport.observation_id == observation_id))
    ).scalars().first()

    score_row = (
        await db.execute(select(SuspicionScore).where(SuspicionScore.observation_id == observation_id))
    ).scalars().first()
    score_factors = []
    suspicion_score = None
    if score_row is not None:
        score_factors = (
            await db.execute(
                select(SuspicionScoreFactor).where(
                    SuspicionScoreFactor.suspicion_score_id == score_row.id
                )
            )
        ).scalars().all()
        suspicion_score = serialize_score(score_row, score_factors)

    review_rows = (
        await db.execute(
            select(AnalystReview, User)
            .join(User, User.id == AnalystReview.analyst_id)
            .where(AnalystReview.observation_id == observation_id)
            .order_by(AnalystReview.updated_at.desc())
        )
    ).all()

    feedback_rows = (
        await db.execute(
            select(AnalystFeedbackEvent, User)
            .join(User, User.id == AnalystFeedbackEvent.analyst_id)
            .where(AnalystFeedbackEvent.observation_id == observation_id)
            .order_by(AnalystFeedbackEvent.created_at.desc())
        )
    ).all()

    return ObservationAnalyticDetailResponse(
        **base_response.model_dump(),
        algorithm_results=algorithm_results,
        suspicion_score=suspicion_score,
        analyst_reviews=[
            serialize_analyst_review(review, analyst.full_name) for review, analyst in review_rows
        ],
        feedback_events=[
            serialize_analyst_feedback(feedback, analyst.full_name)
            for feedback, analyst in feedback_rows
        ],
        suspicion_report=suspicion_report_row,
    )


@router.post("/reviews", response_model=AnalystReviewResponse)
async def create_review(
    payload: AnalystReviewCreateRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    observation = (
        await db.execute(
            scoped_query(
                select(VehicleObservation).where(VehicleObservation.id == payload.observation_id),
                current_user,
                VehicleObservation.agency_id,
            )
        )
    ).scalars().first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observacao nao encontrada")

    if payload.linked_case_id is not None:
        linked_case = (
            await db.execute(
                scoped_query(
                    select(IntelligenceCase).where(IntelligenceCase.id == payload.linked_case_id),
                    current_user,
                    IntelligenceCase.agency_id,
                )
            )
        ).scalars().first()
        if linked_case is None:
            raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    existing = (
        await db.execute(
            select(AnalystReview).where(
                and_(
                    AnalystReview.observation_id == payload.observation_id,
                    AnalystReview.analyst_id == current_user.id,
                )
            )
        )
    ).scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Analista ja possui revisao estruturada para esta observacao",
        )

    review = AnalystReview(
        observation_id=payload.observation_id,
        analyst_id=current_user.id,
        status=payload.status,
        conclusion=payload.conclusion,
        decision=payload.decision,
        source_quality=payload.source_quality,
        data_reliability=payload.data_reliability,
        reinforcing_factors=payload.reinforcing_factors,
        weakening_factors=payload.weakening_factors,
        recommendation=payload.recommendation,
        justification=payload.justification,
        sensitivity_level=payload.sensitivity_level,
        review_due_at=payload.review_due_at,
        linked_case_id=payload.linked_case_id,
        linked_occurrence_ref=payload.linked_occurrence_ref,
    )
    db.add(review)
    await db.flush()
    await create_review_version(
        db,
        review,
        changed_by=current_user.id,
        change_reason=payload.change_reason,
    )
    await log_audit_event(
        db,
        actor=current_user,
        action="analyst_review_created",
        resource_type="analyst_review",
        resource_id=review.id,
        details={"observation_id": str(review.observation_id), "status": review.status.value},
        justification=review.justification,
    )
    await event_bus.publish(
        "analyst_review_created",
        {
            "payload_version": "v1",
            "review_id": str(review.id),
            "observation_id": str(review.observation_id),
            "analyst_id": str(current_user.id),
            "status": review.status.value,
        },
    )
    return serialize_analyst_review(review, current_user.full_name)


@router.patch("/reviews/{review_id}", response_model=AnalystReviewResponse)
async def update_review(
    review_id: UUID,
    payload: AnalystReviewUpdateRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    review = (
        await db.execute(select(AnalystReview).where(AnalystReview.id == review_id))
    ).scalars().first()
    if review is None:
        raise HTTPException(status_code=404, detail="Revisao nao encontrada")
    observation_for_review = (
        await db.execute(
            select(VehicleObservation).where(VehicleObservation.id == review.observation_id)
        )
    ).scalars().first()
    if observation_for_review is None:
        raise HTTPException(status_code=404, detail="Observacao da revisao nao encontrada")
    if current_user.role != UserRole.ADMIN and observation_for_review.agency_id != current_user.agency_id:
        raise HTTPException(status_code=404, detail="Revisao nao encontrada")

    if payload.linked_case_id is not None:
        linked_case = (
            await db.execute(
                scoped_query(
                    select(IntelligenceCase).where(IntelligenceCase.id == payload.linked_case_id),
                    current_user,
                    IntelligenceCase.agency_id,
                )
            )
        ).scalars().first()
        if linked_case is None:
            raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    updates = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    for field, value in updates.items():
        setattr(review, field, value)

    await db.flush()
    await create_review_version(
        db,
        review,
        changed_by=current_user.id,
        change_reason=payload.change_reason,
    )
    await log_audit_event(
        db,
        actor=current_user,
        action="analyst_review_updated",
        resource_type="analyst_review",
        resource_id=review.id,
        details={"observation_id": str(review.observation_id), "status": review.status.value},
        justification=payload.change_reason or review.justification,
    )
    await event_bus.publish(
        "analyst_review_updated",
        {
            "payload_version": "v1",
            "review_id": str(review.id),
            "observation_id": str(review.observation_id),
            "analyst_id": str(current_user.id),
            "status": review.status.value,
        },
    )
    return serialize_analyst_review(review, current_user.full_name)


@router.get("/feedback/pending", response_model=list[FeedbackForAgent])
async def get_pending_feedback(
    current_user: User = Depends(require_field_capable_user),
    db: AsyncSession = Depends(get_db),
):
    feedbacks = await fetch_pending_feedback_for_user(
        db,
        user=current_user,
        unread_only=True,
    )
    record_feedback_pending(pending_count=len(feedbacks), success=True)
    return feedbacks


@router.post("/feedback", response_model=AnalystFeedbackResponse)
async def create_feedback(
    payload: AnalystFeedbackCreateRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    template = None
    if payload.template_id:
        template = (
            await db.execute(
                scoped_query(
                    select(AnalystFeedbackTemplate).where(
                        AnalystFeedbackTemplate.id == payload.template_id
                    ),
                    current_user,
                    AnalystFeedbackTemplate.agency_id,
                )
            )
        ).scalars().first()
        if template is None:
            raise HTTPException(status_code=404, detail="Template de feedback nao encontrado")
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Template de feedback inativo")

    message = payload.message or (template.body_template if template else None)
    if not message:
        raise HTTPException(
            status_code=400,
            detail="Informe mensagem ou template de feedback ativo",
        )

    target_user_id = payload.target_user_id
    if target_user_id is None and payload.observation_id is not None:
        observation = (
            await db.execute(
                scoped_query(
                    select(VehicleObservation).where(VehicleObservation.id == payload.observation_id),
                    current_user,
                    VehicleObservation.agency_id,
                )
            )
        ).scalars().first()
        if observation is None:
            raise HTTPException(status_code=404, detail="Observacao nao encontrada")
        target_user_id = observation.agent_id

    if target_user_id is None and not payload.target_team_label:
        raise HTTPException(
            status_code=400,
            detail="Informe usuario destinatario, equipe alvo ou observacao de origem",
        )

    feedback = AnalystFeedbackEvent(
        agency_id=current_user.agency_id,
        observation_id=payload.observation_id,
        analyst_id=current_user.id,
        target_user_id=target_user_id,
        target_team_label=payload.target_team_label,
        feedback_type=payload.feedback_type,
        sensitivity_level=payload.sensitivity_level,
        title=payload.title,
        message=message,
        template_id=payload.template_id,
        delivered_at=datetime.utcnow(),
    )
    db.add(feedback)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="analyst_feedback_sent",
        resource_type="analyst_feedback",
        resource_id=feedback.id,
        details={
            "observation_id": str(feedback.observation_id) if feedback.observation_id else None,
            "target_user_id": str(feedback.target_user_id) if feedback.target_user_id else None,
            "target_team_label": feedback.target_team_label,
            "feedback_type": feedback.feedback_type,
        },
        justification=feedback.message,
    )
    await event_bus.publish(
        "analyst_feedback_sent",
        {
            "payload_version": "v1",
            "feedback_id": str(feedback.id),
            "observation_id": str(feedback.observation_id) if feedback.observation_id else None,
            "analyst_id": str(current_user.id),
            "target_user_id": str(feedback.target_user_id) if feedback.target_user_id else None,
            "feedback_type": feedback.feedback_type,
        },
    )
    
    # Send WebSocket notification to target user if enabled
    if settings.websocket_enabled and feedback.target_user_id:
        await websocket_manager.send_to_user(
            str(feedback.target_user_id),
            {
                "type": "feedback_received",
                "feedback_id": str(feedback.id),
                "observation_id": str(feedback.observation_id) if feedback.observation_id else None,
                "feedback_type": feedback.feedback_type,
                "title": feedback.title,
                "message": feedback.message,
                "sent_at": feedback.delivered_at.isoformat() if feedback.delivered_at else None,
            }
        )
    
    record_feedback_sent(success=True)
    return serialize_analyst_feedback(feedback, current_user.full_name)


@router.get("/feedback/templates", response_model=list[AnalystFeedbackTemplateResponse])
async def list_feedback_templates(
    active_only: bool = True,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AnalystFeedbackTemplate, User)
        .join(User, User.id == AnalystFeedbackTemplate.created_by)
        .order_by(desc(AnalystFeedbackTemplate.updated_at))
    )
    query = scoped_query(query, current_user, AnalystFeedbackTemplate.agency_id)
    if active_only:
        query = query.where(AnalystFeedbackTemplate.is_active.is_(True))

    rows = (await db.execute(query)).all()
    return [
        serialize_feedback_template(template, creator.full_name)
        for template, creator in rows
    ]


@router.post("/feedback/templates", response_model=AnalystFeedbackTemplateResponse)
async def create_feedback_template(
    payload: AnalystFeedbackTemplateCreateRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    template = AnalystFeedbackTemplate(
        agency_id=current_user.agency_id,
        created_by=current_user.id,
        name=payload.name,
        feedback_type=payload.feedback_type,
        sensitivity_level=payload.sensitivity_level,
        body_template=payload.body_template,
        is_active=payload.is_active,
    )
    db.add(template)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="analyst_feedback_template_created",
        resource_type="analyst_feedback_template",
        resource_id=template.id,
        details={
            "name": template.name,
            "feedback_type": template.feedback_type,
            "sensitivity_level": template.sensitivity_level,
            "is_active": template.is_active,
        },
    )
    return serialize_feedback_template(template, current_user.full_name)


@router.get("/feedback/recipients", response_model=list[FeedbackRecipientResponse])
async def list_feedback_recipients(
    query: str | None = None,
    limit: int = 20,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    capped_limit = max(1, min(limit, 100))
    search_query = query.strip() if query else None

    user_query = (
        select(User, Unit)
        .outerjoin(Unit, Unit.id == User.unit_id)
        .where(User.is_active.is_(True))
        .where(User.role.in_([UserRole.FIELD_AGENT, UserRole.SUPERVISOR]))
        .order_by(User.full_name.asc())
        .limit(capped_limit)
    )
    user_query = scoped_query(user_query, current_user, User.agency_id)
    if search_query:
        user_query = user_query.where(
            or_(
                User.full_name.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.badge_number.ilike(f"%{search_query}%"),
                Unit.name.ilike(f"%{search_query}%"),
                Unit.code.ilike(f"%{search_query}%"),
            )
        )

    user_rows = (await db.execute(user_query)).all()
    recipients: list[FeedbackRecipientResponse] = []
    seen_team_labels: set[str] = set()

    for user_row, unit in user_rows:
        unit_code = unit.code if unit is not None else None
        recipients.append(
            FeedbackRecipientResponse(
                recipient_type="user",
                user_id=user_row.id,
                user_name=user_row.full_name,
                user_role=user_row.role.value,
                unit_id=unit.id if unit is not None else None,
                unit_code=unit_code,
                unit_name=unit.name if unit is not None else None,
                target_team_label=unit_code,
                label=f"{user_row.full_name} ({unit_code or 'SEM-UNIDADE'})",
            )
        )
        if unit_code and unit_code not in seen_team_labels:
            seen_team_labels.add(unit_code)
            recipients.append(
                FeedbackRecipientResponse(
                    recipient_type="unit",
                    unit_id=unit.id if unit is not None else None,
                    unit_code=unit_code,
                    unit_name=unit.name if unit is not None else None,
                    target_team_label=unit_code,
                    label=f"{unit_code} - {unit.name if unit is not None else 'Unidade'}",
                )
            )

    return recipients[: capped_limit * 2]


@router.post("/feedback/{feedback_id}/read")
async def mark_feedback_read(
    feedback_id: UUID,
    payload: MarkFeedbackReadRequest,
    current_user: User = Depends(require_field_capable_user),
    db: AsyncSession = Depends(get_db),
):
    recipient_filters = [AnalystFeedbackEvent.target_user_id == current_user.id]
    unit_code = None
    if current_user.unit_id:
        unit = (
            await db.execute(select(Unit).where(Unit.id == current_user.unit_id))
        ).scalar_one_or_none()
        unit_code = unit.code if unit is not None else None
    if unit_code:
        recipient_filters.append(AnalystFeedbackEvent.target_team_label == unit_code)

    structured_feedback = (
        await db.execute(
            select(AnalystFeedbackEvent).where(
                and_(
                    AnalystFeedbackEvent.id == feedback_id,
                    AnalystFeedbackEvent.agency_id == current_user.agency_id,
                    or_(*recipient_filters),
                )
            )
        )
    ).scalars().first()
    if structured_feedback is not None:
        structured_feedback.read_at = payload.read_at
        await log_audit_event(
            db,
            actor=current_user,
            action="analyst_feedback_read",
            resource_type="analyst_feedback_event",
            resource_id=structured_feedback.id,
            details={"read_at": payload.read_at.isoformat()},
        )
        record_feedback_read(success=True)
        return {"message": "Feedback marcado como lido"}

    legacy_result = await db.execute(
        select(FeedbackEvent).where(
            and_(
                FeedbackEvent.id == feedback_id,
                FeedbackEvent.target_agent_id == current_user.id,
            )
        )
    )
    feedback = legacy_result.scalar_one_or_none()
    if feedback is None:
        raise HTTPException(status_code=404, detail="Feedback nao encontrado")

    feedback.read_at = payload.read_at
    await log_audit_event(
        db,
        actor=current_user,
        action="field_feedback_read",
        resource_type="feedback_event",
        resource_id=feedback.id,
        details={"read_at": payload.read_at.isoformat()},
    )
    record_feedback_read(success=True)
    return {"message": "Feedback marcado como lido"}


@router.get("/watchlist", response_model=list[WatchlistEntryResponse])
@router.get("/watchlists", response_model=list[WatchlistEntryResponse])
async def list_watchlist(
    status: WatchlistStatus | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(WatchlistEntry, User)
        .join(User, User.id == WatchlistEntry.created_by)
        .order_by(WatchlistEntry.priority.asc(), WatchlistEntry.created_at.desc())
    )
    query = scoped_query(query, current_user, WatchlistEntry.agency_id)
    if status is not None:
        query = query.where(WatchlistEntry.status == status)

    rows = (await db.execute(query)).all()
    return [serialize_watchlist_entry(entry, creator.full_name) for entry, creator in rows]


@router.post("/watchlist", response_model=WatchlistEntryResponse)
@router.post("/watchlists", response_model=WatchlistEntryResponse)
async def create_watchlist_entry(
    payload: WatchlistEntryCreate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    entry = WatchlistEntry(
        agency_id=current_user.agency_id,
        created_by=current_user.id,
        status=payload.status,
        category=payload.category,
        plate_number=payload.plate_number,
        plate_partial=payload.plate_partial,
        vehicle_make=payload.vehicle_make,
        vehicle_model=payload.vehicle_model,
        vehicle_color=payload.vehicle_color,
        visual_traits=payload.visual_traits,
        interest_reason=payload.interest_reason,
        information_source=payload.information_source,
        sensitivity_level=payload.sensitivity_level,
        confidence_level=payload.confidence_level,
        geographic_scope=payload.geographic_scope,
        active_time_window=payload.active_time_window,
        priority=payload.priority,
        recommended_action=payload.recommended_action,
        silent_mode=payload.silent_mode,
        notes=payload.notes,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        review_due_at=payload.review_due_at,
        metadata_json=payload.metadata_json,
    )
    db.add(entry)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="watchlist_created",
        resource_type="watchlist_entry",
        resource_id=entry.id,
        details={"category": entry.category.value, "status": entry.status.value},
        justification=entry.interest_reason,
    )
    return serialize_watchlist_entry(entry, current_user.full_name)


@router.patch("/watchlist/{entry_id}", response_model=WatchlistEntryResponse)
@router.patch("/watchlists/{entry_id}", response_model=WatchlistEntryResponse)
async def update_watchlist_entry(
    entry_id: UUID,
    payload: WatchlistEntryUpdate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        scoped_query(
            select(WatchlistEntry).where(WatchlistEntry.id == entry_id),
            current_user,
            WatchlistEntry.agency_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Cadastro de watchlist nao encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="watchlist_updated",
        resource_type="watchlist_entry",
        resource_id=entry.id,
        details=payload.model_dump(exclude_unset=True),
    )
    return serialize_watchlist_entry(entry, current_user.full_name)


@router.delete("/watchlist/{entry_id}")
@router.delete("/watchlists/{entry_id}")
async def delete_watchlist_entry(
    entry_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        scoped_query(
            select(WatchlistEntry).where(WatchlistEntry.id == entry_id),
            current_user,
            WatchlistEntry.agency_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Cadastro de watchlist nao encontrado")

    await db.delete(entry)
    await log_audit_event(
        db,
        actor=current_user,
        action="watchlist_deleted",
        resource_type="watchlist_entry",
        resource_id=entry.id,
        details={"plate_number": entry.plate_number, "status": entry.status.value},
    )
    return {"message": "Cadastro de watchlist excluído com sucesso"}


@router.get("/routes", response_model=list[AlgorithmResultResponse])
async def list_route_anomalies(
    plate_number: str | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(RouteAnomalyEvent)
        .join(VehicleObservation, VehicleObservation.id == RouteAnomalyEvent.observation_id)
        .order_by(desc(RouteAnomalyEvent.created_at))
        .limit(100)
    )
    query = scoped_query(query, current_user, VehicleObservation.agency_id)
    if plate_number:
        query = query.where(RouteAnomalyEvent.plate_number == plate_number.upper())

    rows = (await db.execute(query)).scalars().all()
    return [
        serialize_algorithm_result(
            event_id=row.id,
            algorithm_type="route_anomaly",
            observation_id=row.observation_id,
            plate_number=row.plate_number,
            decision=row.decision,
            confidence=row.confidence,
            severity=row.severity,
            explanation=row.explanation,
            false_positive_risk=row.false_positive_risk,
            metrics={
                "region_from_id": str(row.region_from_id) if row.region_from_id else None,
                "region_to_id": str(row.region_to_id) if row.region_to_id else None,
                "anomaly_score": row.anomaly_score,
            },
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/convoys", response_model=list[AlgorithmResultResponse])
async def list_convoys(
    plate_number: str | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ConvoyEvent)
        .join(VehicleObservation, VehicleObservation.id == ConvoyEvent.observation_id)
        .order_by(desc(ConvoyEvent.created_at))
        .limit(100)
    )
    query = scoped_query(query, current_user, VehicleObservation.agency_id)
    if plate_number:
        query = query.where(
            or_(
                ConvoyEvent.primary_plate == plate_number.upper(),
                ConvoyEvent.related_plate == plate_number.upper(),
            )
        )

    rows = (await db.execute(query)).scalars().all()
    return [
        serialize_algorithm_result(
            event_id=row.id,
            algorithm_type="convoy",
            observation_id=row.observation_id,
            plate_number=row.primary_plate,
            decision=row.decision,
            confidence=row.confidence,
            severity=row.severity,
            explanation=row.explanation,
            false_positive_risk=row.false_positive_risk,
            metrics={
                "related_plate": row.related_plate,
                "cooccurrence_count": row.cooccurrence_count,
            },
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/roaming", response_model=list[AlgorithmResultResponse])
async def list_roaming_events(
    plate_number: str | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(RoamingEvent)
        .join(VehicleObservation, VehicleObservation.id == RoamingEvent.observation_id)
        .order_by(desc(RoamingEvent.created_at))
        .limit(100)
    )
    query = scoped_query(query, current_user, VehicleObservation.agency_id)
    if plate_number:
        query = query.where(RoamingEvent.plate_number == plate_number.upper())

    rows = (await db.execute(query)).scalars().all()
    return [
        serialize_algorithm_result(
            event_id=row.id,
            algorithm_type="roaming",
            observation_id=row.observation_id,
            plate_number=row.plate_number,
            decision=row.decision,
            confidence=row.confidence,
            severity=row.severity,
            explanation=row.explanation,
            false_positive_risk=row.false_positive_risk,
            metrics={"area_label": row.area_label, "recurrence_count": row.recurrence_count},
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/sensitive-assets", response_model=list[AlgorithmResultResponse])
async def list_sensitive_asset_events(
    plate_number: str | None = None,
    zone_id: UUID | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(SensitiveAssetRecurrenceEvent)
        .join(VehicleObservation, VehicleObservation.id == SensitiveAssetRecurrenceEvent.observation_id)
        .order_by(desc(SensitiveAssetRecurrenceEvent.created_at))
        .limit(100)
    )
    query = scoped_query(query, current_user, VehicleObservation.agency_id)
    if plate_number:
        query = query.where(SensitiveAssetRecurrenceEvent.plate_number == plate_number.upper())
    if zone_id:
        query = query.where(SensitiveAssetRecurrenceEvent.zone_id == zone_id)

    rows = (await db.execute(query)).scalars().all()
    return [
        serialize_algorithm_result(
            event_id=row.id,
            algorithm_type="sensitive_zone_recurrence",
            observation_id=row.observation_id,
            plate_number=row.plate_number,
            decision=row.decision,
            confidence=row.confidence,
            severity=row.severity,
            explanation=row.explanation,
            false_positive_risk=row.false_positive_risk,
            metrics={"zone_id": str(row.zone_id), "recurrence_count": row.recurrence_count},
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/cases", response_model=list[IntelligenceCaseResponse])
async def list_cases(
    status: CaseStatus | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(IntelligenceCase, User)
        .join(User, User.id == IntelligenceCase.created_by)
        .order_by(IntelligenceCase.priority.asc(), desc(IntelligenceCase.updated_at))
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    query = scoped_query(query, current_user, IntelligenceCase.agency_id)
    if status:
        query = query.where(IntelligenceCase.status == status)
    if search:
        query = query.where(
            or_(
                IntelligenceCase.title.ilike(f"%{search}%"),
                IntelligenceCase.hypothesis.ilike(f"%{search}%"),
                IntelligenceCase.summary.ilike(f"%{search}%"),
            )
        )

    rows = (await db.execute(query)).all()
    return [serialize_case(case_row, creator.full_name) for case_row, creator in rows]


@router.post("/cases", response_model=IntelligenceCaseResponse)
async def create_case(
    payload: IntelligenceCaseCreate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = IntelligenceCase(
        agency_id=current_user.agency_id,
        created_by=current_user.id,
        title=payload.title,
        hypothesis=payload.hypothesis,
        summary=payload.summary,
        status=payload.status,
        sensitivity_level=payload.sensitivity_level,
        priority=payload.priority,
        review_due_at=payload.review_due_at,
    )
    db.add(case_row)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="intelligence_case_created",
        resource_type="intelligence_case",
        resource_id=case_row.id,
        details={"status": case_row.status.value, "priority": case_row.priority},
        justification=case_row.hypothesis or case_row.summary,
    )
    await event_bus.publish(
        "intelligence_case_created",
        {
            "payload_version": "v1",
            "case_id": str(case_row.id),
            "created_by": str(current_user.id),
            "status": case_row.status.value,
        },
    )
    return serialize_case(case_row, current_user.full_name)


@router.get("/cases/{case_id}", response_model=IntelligenceCaseResponse)
async def get_case(
    case_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")
    
    creator = (
        await db.execute(select(User).where(User.id == case_row.created_by))
    ).scalars().first()
    
    return serialize_case(case_row, creator.full_name if creator else None)


@router.patch("/cases/{case_id}", response_model=IntelligenceCaseResponse)
async def update_case(
    case_id: UUID,
    payload: IntelligenceCaseUpdate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case_row, field, value)

    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="intelligence_case_updated",
        resource_type="intelligence_case",
        resource_id=case_row.id,
        details=payload.model_dump(exclude_unset=True),
        justification=case_row.hypothesis or case_row.summary,
    )
    return serialize_case(case_row, current_user.full_name)


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    await db.delete(case_row)
    await log_audit_event(
        db,
        actor=current_user,
        action="intelligence_case_deleted",
        resource_type="intelligence_case",
        resource_id=case_row.id,
        details={"title": case_row.title, "status": case_row.status.value},
        justification=case_row.hypothesis or case_row.summary,
    )
    return {"message": "Caso analitico excluído com sucesso"}


@router.get("/cases/{case_id}/links", response_model=list[CaseLinkResponse])
async def list_case_links(
    case_id: UUID,
    link_type: CaseLinkType | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    query = select(CaseLink, User).join(User, User.id == CaseLink.created_by).where(CaseLink.case_id == case_id)
    if link_type:
        query = query.where(CaseLink.link_type == link_type)
    query = query.order_by(CaseLink.created_at.desc())

    rows = (await db.execute(query)).all()
    return [serialize_case_link(link, creator.full_name) for link, creator in rows]


@router.post("/cases/{case_id}/links", response_model=CaseLinkResponse)
async def add_case_link(
    case_id: UUID,
    payload: CaseLinkCreate,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    link = CaseLink(
        case_id=case_id,
        link_type=payload.link_type,
        linked_entity_id=payload.linked_entity_id,
        linked_label=payload.linked_label,
        created_by=current_user.id,
    )
    db.add(link)
    await db.flush()
    await log_audit_event(
        db,
        actor=current_user,
        action="case_link_created",
        resource_type="case_link",
        resource_id=link.id,
        details={"link_type": link.link_type.value, "entity_id": str(link.linked_entity_id)},
    )
    return serialize_case_link(link, current_user.full_name)


@router.delete("/cases/{case_id}/links/{link_id}")
async def remove_case_link(
    case_id: UUID,
    link_id: UUID,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    case_row = (
        await db.execute(
            scoped_query(
                select(IntelligenceCase).where(IntelligenceCase.id == case_id),
                current_user,
                IntelligenceCase.agency_id,
            )
        )
    ).scalars().first()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Caso analitico nao encontrado")

    link = (
        await db.execute(
            select(CaseLink).where(CaseLink.id == link_id, CaseLink.case_id == case_id)
        )
    ).scalars().first()
    if link is None:
        raise HTTPException(status_code=404, detail="Vinculo de caso nao encontrado")

    await db.delete(link)
    await log_audit_event(
        db,
        actor=current_user,
        action="case_link_deleted",
        resource_type="case_link",
        resource_id=link.id,
        details={"link_type": link.link_type.value, "entity_id": str(link.linked_entity_id)},
    )
    return {"message": "Vinculo de caso removido com sucesso"}


@router.get("/analytics/overview")
async def get_analytics_overview(
    agency_id: Optional[str] = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics overview with optional agency filter.
    Users can filter by agencies within their scope based on hierarchy.
    """
    now = datetime.utcnow()
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_30_days = now - timedelta(days=30)
    
    # Apply agency filter based on user role and hierarchy
    if current_user.role == UserRole.ADMIN:
        # ADMIN can see all or filter by specific agency
        agency_filter = true() if agency_id is None else VehicleObservation.agency_id == agency_id
    else:
        # Other users can only see their agency or child agencies (for regional/central)
        # For now, simple agency filter - can be extended with hierarchy
        if agency_id is not None and agency_id != str(current_user.agency_id):
            raise HTTPException(status_code=403, detail="Usuario sem acesso a essa agencia")
        agency_filter = VehicleObservation.agency_id == current_user.agency_id

    total_observations = (
        await db.execute(select(func.count(VehicleObservation.id)).where(agency_filter))
    ).scalar() or 0
    today_observations = (
        await db.execute(
            select(func.count(VehicleObservation.id)).where(
                VehicleObservation.observed_at_local >= start_today,
                agency_filter,
            )
        )
    ).scalar() or 0
    pending_reviews = (
        await db.execute(
            select(func.count(SuspicionReport.id))
            .join(VehicleObservation, VehicleObservation.id == SuspicionReport.observation_id)
            .outerjoin(AnalystReview, AnalystReview.observation_id == VehicleObservation.id)
            .where(AnalystReview.id.is_(None), agency_filter)
        )
    ).scalar() or 0
    active_alerts = (
        await db.execute(
            select(func.count(AnalystFeedbackEvent.id)).where(AnalystFeedbackEvent.read_at.is_(None))
        )
    ).scalar() or 0
    confirmed_suspicions = (
        await db.execute(
            select(func.count(AnalystReview.id)).where(AnalystReview.decision.is_not(None))
        )
    ).scalar() or 0
    discarded_suspicions = (
        await db.execute(
            select(func.count(AnalystReview.id)).where(AnalystReview.decision == "discarded")
        )
    ).scalar() or 0
    avg_response_time_hours = (
        await db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        AnalystReview.updated_at - VehicleObservation.observed_at_local,
                    )
                    / 3600.0
                )
            )
            .select_from(AnalystReview)
            .join(VehicleObservation, VehicleObservation.id == AnalystReview.observation_id)
            .where(AnalystReview.updated_at >= last_30_days, agency_filter)
        )
    ).scalar()
    corrected_rate = (
        await db.execute(
            select(
                func.avg(
                    case(
                        (
                            func.upper(func.replace(PlateRead.ocr_raw_text, "-", ""))
                            != VehicleObservation.plate_number,
                            1.0,
                        ),
                        else_=0.0,
                    )
                )
            )
            .select_from(PlateRead)
            .join(VehicleObservation, VehicleObservation.id == PlateRead.observation_id)
            .where(PlateRead.processed_at >= last_30_days, agency_filter)
        )
    ).scalar()
    critical_scores = (
        await db.execute(
            select(func.count(SuspicionScore.id)).where(SuspicionScore.final_label == "critical")
        )
    ).scalar() or 0
    watchlist_hits = (
        await db.execute(
            select(func.count(WatchlistHit.id))
            .join(VehicleObservation, VehicleObservation.id == WatchlistHit.observation_id)
            .where(agency_filter)
        )
    ).scalar() or 0

    return {
        "total_observations": total_observations,
        "today_observations": today_observations,
        "pending_reviews": pending_reviews,
        "active_alerts": active_alerts,
        "confirmed_suspicions": confirmed_suspicions,
        "discarded_suspicions": discarded_suspicions,
        "avg_response_time_hours": float(avg_response_time_hours or 0.0),
        "ocr_correction_rate": float(corrected_rate or 0.0),
        "critical_scores": critical_scores,
        "watchlist_hits": watchlist_hits,
    }


@router.get("/analytics/observations-by-day")
async def get_observations_by_day(
    days: int = 7,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    days = max(1, min(days, 90))
    start = datetime.utcnow() - timedelta(days=days)
    agency_filter = (
        true() if current_user.role == UserRole.ADMIN else VehicleObservation.agency_id == current_user.agency_id
    )
    rows = (
        await db.execute(
            select(
                func.date_trunc("day", VehicleObservation.observed_at_local).label("bucket"),
                func.count(VehicleObservation.id).label("count"),
            )
            .where(VehicleObservation.observed_at_local >= start, agency_filter)
            .group_by("bucket")
            .order_by("bucket")
        )
    ).all()
    return [
        {"date": bucket.date().isoformat(), "count": int(count)}
        for bucket, count in rows
    ]


@router.get("/agencies")
async def list_agencies(
    agency_type: str | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    List agencies with optional filter by type (local/regional/central).
    Users can only see agencies within their scope based on hierarchy.
    """
    from app.db.base import AgencyType
    
    query = select(Agency).where(Agency.is_active == True)
    
    # Filter by type if specified
    if agency_type:
        try:
            agency_type_enum = AgencyType(agency_type)
            query = query.where(Agency.type == agency_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agency type: {agency_type}")
    
    # Apply agency scope filter based on user role and hierarchy
    if current_user.role != UserRole.ADMIN:
        # For now, simple filter - user sees their own agency
        # TODO: Implement full hierarchy filtering (child agencies)
        query = query.where(Agency.id == current_user.agency_id)
    
    result = await db.execute(query)
    agencies = result.scalars().all()
    
    return AgencyListResponse(
        agencies=[AgencyResponse.model_validate(agency) for agency in agencies],
        total=len(agencies),
    )


@router.get("/analytics/top-plates")
async def get_top_plates(
    limit: int = 10,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    agency_filter = (
        true() if current_user.role == UserRole.ADMIN else VehicleObservation.agency_id == current_user.agency_id
    )
    rows = (
        await db.execute(
            select(
                VehicleObservation.plate_number,
                func.count(VehicleObservation.id).label("observation_count"),
                func.count(SuspicionReport.id).label("suspicion_count"),
            )
            .outerjoin(SuspicionReport, SuspicionReport.observation_id == VehicleObservation.id)
            .where(agency_filter)
            .group_by(VehicleObservation.plate_number)
            .order_by(desc("observation_count"))
            .limit(limit)
        )
    ).all()
    return [
        {
            "plate_number": plate_number,
            "observation_count": int(observation_count),
            "suspicion_count": int(suspicion_count),
        }
        for plate_number, observation_count, suspicion_count in rows
    ]


@router.get("/analytics/unit-performance")
async def get_unit_performance(
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    agency_filter = (
        true() if current_user.role == UserRole.ADMIN else VehicleObservation.agency_id == current_user.agency_id
    )
    rows = (
        await db.execute(
            select(
                Unit.id,
                Unit.name,
                func.count(VehicleObservation.id).label("observation_count"),
                func.avg(
                    case(
                        (AnalystReview.decision.is_not(None), 1.0),
                        else_=0.0,
                    )
                ).label("confirmation_rate"),
            )
            .join(User, User.unit_id == Unit.id)
            .join(VehicleObservation, VehicleObservation.agent_id == User.id)
            .outerjoin(AnalystReview, AnalystReview.observation_id == VehicleObservation.id)
            .where(agency_filter)
            .group_by(Unit.id, Unit.name)
            .order_by(desc("observation_count"))
        )
    ).all()
    return [
        {
            "unit_id": str(unit_id),
            "unit_name": unit_name,
            "observation_count": int(observation_count),
            "confirmation_rate": float(confirmation_rate or 0.0),
        }
        for unit_id, unit_name, observation_count, confirmation_rate in rows
    ]


@router.post("/route-analysis", response_model=RoutePatternResponse)
async def analyze_vehicle_route_endpoint(
    request: RouteAnalysisRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Analyze route patterns for a vehicle."""
    result = await analyze_vehicle_route(
        db,
        plate_number=request.plate_number,
        agency_id=current_user.agency_id,
        start_date=request.start_date,
        end_date=request.end_date,
        min_observations=request.min_observations
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient observations for route analysis of plate {request.plate_number}"
        )

    pattern = await save_route_pattern(db, result, current_user.agency_id)
    centroid_shape = to_shape(pattern.centroid_location)
    bounding_box_shape = to_shape(pattern.bounding_box)
    bounding_coords = list(bounding_box_shape.exterior.coords)[:-1]
    corridor_points = None
    if pattern.corridor is not None:
        corridor_shape = to_shape(pattern.corridor)
        corridor_points = [
            GeolocationPoint(latitude=lat, longitude=lng)
            for lng, lat in corridor_shape.coords
        ]

    return RoutePatternResponse(
        id=pattern.id,
        plate_number=pattern.plate_number,
        observation_count=pattern.observation_count,
        first_observed_at=pattern.first_observed_at,
        last_observed_at=pattern.last_observed_at,
        centroid=GeolocationPoint(latitude=centroid_shape.y, longitude=centroid_shape.x),
        bounding_box=[
            GeolocationPoint(latitude=lat, longitude=lng)
            for lng, lat in bounding_coords
        ],
        corridor_points=corridor_points,
        primary_corridor_name=pattern.primary_corridor_name,
        predominant_direction=pattern.predominant_direction,
        recurrence_score=pattern.recurrence_score,
        pattern_strength=pattern.pattern_strength,
        common_hours=pattern.common_hours or [],
        common_days=pattern.common_days or [],
        analyzed_at=pattern.analyzed_at,
        analysis_version=pattern.analysis_version,
    )


@router.post("/routes/analyze", response_model=RoutePatternResponse)
async def analyze_vehicle_route_alias(
    request: RouteAnalysisRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Compatibility alias for web clients that call /intelligence/routes/analyze.
    """
    return await analyze_vehicle_route_endpoint(
        request=request,
        current_user=current_user,
        db=db,
    )


@router.get("/route-timeline/{plate_number}", response_model=RouteTimelineResponse)
async def get_vehicle_route_timeline(
    plate_number: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get timeline of observations for route visualization."""
    timeline_items = await get_route_timeline(
        db,
        plate_number=plate_number,
        agency_id=current_user.agency_id,
        start_date=start_date,
        end_date=end_date
    )

    # Calculate stats
    total_observations = len(timeline_items)
    if total_observations == 0:
        raise HTTPException(status_code=404, detail=f"No observations found for plate {plate_number}")

    time_span = timeline_items[-1].timestamp - timeline_items[0].timestamp
    time_span_hours = time_span.total_seconds() / 3600

    unique_agents = len(set(item.agent_name for item in timeline_items))
    unique_units = len(set(item.unit_name for item in timeline_items if item.unit_name))
    suspicion_count = sum(1 for item in timeline_items if item.has_suspicion)

    return RouteTimelineResponse(
        plate_number=plate_number,
        total_observations=total_observations,
        time_span_hours=time_span_hours,
        items=timeline_items,
        unique_agents=unique_agents,
        unique_units=unique_units,
        suspicion_count=suspicion_count
    )


@router.get("/routes/{plate_number}/timeline", response_model=RouteTimelineResponse)
async def get_vehicle_route_timeline_alias(
    plate_number: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Compatibility alias for web clients that call /intelligence/routes/{plate}/timeline.
    """
    return await get_vehicle_route_timeline(
        plate_number=plate_number,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        db=db,
    )


@router.get("/routes/{plate_number}", response_model=RoutePatternResponse)
async def get_latest_route_pattern(
    plate_number: str,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns latest persisted route pattern for a plate.
    If none exists, computes a fresh one with default criteria.
    """
    normalized_plate = plate_number.upper().strip()
    pattern = (
        await db.execute(
            select(RoutePattern)
            .where(
                RoutePattern.plate_number == normalized_plate,
                RoutePattern.agency_id == current_user.agency_id,
            )
            .order_by(desc(RoutePattern.analyzed_at))
            .limit(1)
        )
    ).scalars().first()

    if pattern is None:
        result = await analyze_vehicle_route(
            db,
            plate_number=normalized_plate,
            agency_id=current_user.agency_id,
            min_observations=3,
        )
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient observations for route analysis of plate {normalized_plate}",
            )
        pattern = await save_route_pattern(db, result, current_user.agency_id)

    centroid_shape = to_shape(pattern.centroid_location)
    bounding_box_shape = to_shape(pattern.bounding_box)
    bounding_coords = list(bounding_box_shape.exterior.coords)[:-1]
    corridor_points = None
    if pattern.corridor is not None:
        corridor_shape = to_shape(pattern.corridor)
        corridor_points = [
            GeolocationPoint(latitude=lat, longitude=lng)
            for lng, lat in corridor_shape.coords
        ]

    return RoutePatternResponse(
        id=pattern.id,
        plate_number=pattern.plate_number,
        observation_count=pattern.observation_count,
        first_observed_at=pattern.first_observed_at,
        last_observed_at=pattern.last_observed_at,
        centroid=GeolocationPoint(latitude=centroid_shape.y, longitude=centroid_shape.x),
        bounding_box=[
            GeolocationPoint(latitude=lat, longitude=lng)
            for lng, lat in bounding_coords
        ],
        corridor_points=corridor_points,
        primary_corridor_name=pattern.primary_corridor_name,
        predominant_direction=pattern.predominant_direction,
        recurrence_score=pattern.recurrence_score,
        pattern_strength=pattern.pattern_strength,
        common_hours=pattern.common_hours or [],
        common_days=pattern.common_days or [],
        analyzed_at=pattern.analyzed_at,
        analysis_version=pattern.analysis_version,
    )
