"""
Async worker helpers for FARO analytics.
"""
from sqlalchemy import select

from app.db.base import VehicleObservation
from app.db.session import get_session
from app.services.analytics_service import evaluate_observation_algorithms


async def reprocess_observation(observation_id):
    async with get_session() as session:
        observation = (
            await session.execute(select(VehicleObservation).where(VehicleObservation.id == observation_id))
        ).scalar_one_or_none()
        if observation is None:
            return None
        await evaluate_observation_algorithms(session, observation)
        return observation.id
