"""
Shared feedback retrieval service for field users.
"""
from __future__ import annotations

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    AnalystFeedbackEvent,
    FeedbackEvent,
    IntelligenceReview,
    Unit,
    User,
    VehicleObservation,
)
from app.schemas.intelligence import FeedbackForAgent


async def _resolve_user_unit_code(db: AsyncSession, user: User) -> str | None:
    if not user.unit_id:
        return None
    unit = (
        await db.execute(select(Unit).where(Unit.id == user.unit_id))
    ).scalars().first()
    return unit.code if unit is not None else None


async def fetch_pending_feedback_for_user(
    db: AsyncSession,
    *,
    user: User,
    unread_only: bool = True,
    limit: int | None = None,
) -> list[FeedbackForAgent]:
    unit_code = await _resolve_user_unit_code(db, user)

    structured_filters = [AnalystFeedbackEvent.target_user_id == user.id]
    if unit_code:
        structured_filters.append(AnalystFeedbackEvent.target_team_label == unit_code)

    structured_where = [
        AnalystFeedbackEvent.observation_id.is_not(None),
        AnalystFeedbackEvent.agency_id == user.agency_id,
        or_(*structured_filters),
    ]
    if unread_only:
        structured_where.append(AnalystFeedbackEvent.read_at.is_(None))

    structured_result = await db.execute(
        select(AnalystFeedbackEvent, VehicleObservation, User)
        .join(VehicleObservation, VehicleObservation.id == AnalystFeedbackEvent.observation_id)
        .join(User, User.id == AnalystFeedbackEvent.analyst_id)
        .where(and_(*structured_where))
        .order_by(desc(AnalystFeedbackEvent.created_at))
    )
    structured_items = [
        FeedbackForAgent(
            feedback_id=feedback.id,
            observation_id=observation.id,
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
        for feedback, observation, analyst in structured_result.all()
    ]

    legacy_where = [FeedbackEvent.target_agent_id == user.id]
    if unread_only:
        legacy_where.append(FeedbackEvent.read_at.is_(None))

    legacy_result = await db.execute(
        select(FeedbackEvent, IntelligenceReview, VehicleObservation, User)
        .join(IntelligenceReview, IntelligenceReview.id == FeedbackEvent.review_id)
        .join(VehicleObservation, VehicleObservation.id == IntelligenceReview.observation_id)
        .join(User, User.id == IntelligenceReview.reviewer_id)
        .where(and_(*legacy_where))
        .order_by(desc(FeedbackEvent.sent_at))
    )
    legacy_items = [
        FeedbackForAgent(
            feedback_id=feedback.id,
            observation_id=observation.id,
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
        for feedback, _, observation, reviewer in legacy_result.all()
    ]

    all_items = sorted(
        structured_items + legacy_items,
        key=lambda item: item.sent_at,
        reverse=True,
    )
    if limit is not None:
        return all_items[:limit]
    return all_items
