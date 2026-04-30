"""
Algorithm Validation Service for F.A.R.O.
Integrates autonomous detection algorithms with field validation from UnifiedSuspicionService.
Creates closed feedback loop for continuous learning and optimization.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select, desc

from app.db.base import (
    AlgorithmRun,
    AlgorithmType,
    SuspicionReport,
    VehicleObservation,
)
from app.services.unified_suspicion_service import unified_suspicion_service

logger = logging.getLogger(__name__)


class ValidationFactor(str, Enum):
    """Validation factor levels."""
    SEVERE_PENALTY = "severe_penalty"  # 0.3 - Many false positives
    PENALTY = "penalty"  # 0.7 - Some false positives
    NEUTRAL = "neutral"  # 1.0 - Balanced
    BOOST = "boost"  # 1.3 - High confirmation rate
    STRONG_BOOST = "strong_boost"  # 1.5 - Very high confirmation rate


@dataclass
class ValidationContext:
    """Context for algorithm validation."""
    plate_number: str
    algorithm_type: AlgorithmType
    observation_count: int
    confirmed_count: int
    false_positive_count: int
    confirmation_rate: float
    last_validation_days: int
    validation_factor: float
    recommendation: str


@dataclass
class AdjustedAlgorithmResult:
    """Algorithm result adjusted by validation."""
    original_result: any
    adjusted_score: float
    validation_factor: float
    validation_context: ValidationContext
    should_suppress: bool
    reason: str


class AlgorithmValidationService:
    """
    Service for validating and adjusting algorithm results based on field validation.
    Creates closed feedback loop between autonomous detection and field confirmation.
    """
    
    def __init__(self):
        self.cache_ttl = timedelta(hours=1)
    
    async def validate_algorithm_result(
        self,
        db: AsyncSession,
        algorithm_type: AlgorithmType,
        observation: VehicleObservation,
        original_result: any,
        original_score: Optional[float] = None
    ) -> AdjustedAlgorithmResult:
        """
        Validate algorithm result against field validation history.
        
        Args:
            db: Database session
            algorithm_type: Type of algorithm being validated
            observation: Vehicle observation
            original_result: Original algorithm result
            original_score: Original algorithm score (if applicable)
            
        Returns:
            Adjusted algorithm result with validation context
        """
        # Get validation context
        context = await self.get_validation_context(
            db,
            observation.plate_number,
            algorithm_type
        )
        
        # Calculate validation factor
        validation_factor = context.validation_factor
        
        # Adjust score if provided
        adjusted_score = original_score
        if original_score is not None:
            adjusted_score = original_score * validation_factor
        
        # Determine if result should be suppressed
        should_suppress, reason = self.determine_suppression(
            context, original_result
        )
        
        return AdjustedAlgorithmResult(
            original_result=original_result,
            adjusted_score=adjusted_score,
            validation_factor=validation_factor,
            validation_context=context,
            should_suppress=should_suppress,
            reason=reason
        )
    
    async def get_validation_context(
        self,
        db: AsyncSession,
        plate_number: str,
        algorithm_type: AlgorithmType,
        days: int = 90
    ) -> ValidationContext:
        """
        Get validation context for a plate and algorithm type.
        
        Args:
            db: Database session
            plate_number: Vehicle plate number
            algorithm_type: Algorithm type
            days: Number of days to analyze
            
        Returns:
            Validation context with metrics
        """
        # Get suspicion history from UnifiedSuspicionService
        suspicion_history = await unified_suspicion_service.get_suspicion_history(
            db, plate_number, limit=50
        )
        
        if not suspicion_history:
            # No history - neutral validation
            return ValidationContext(
                plate_number=plate_number,
                algorithm_type=algorithm_type,
                observation_count=0,
                confirmed_count=0,
                false_positive_count=0,
                confirmation_rate=0.0,
                last_validation_days=days,
                validation_factor=1.0,
                recommendation="No validation history - neutral"
            )
        
        # Filter by algorithm trigger if available
        relevant_history = [
            s for s in suspicion_history
            if not s.triggered_by or s.triggered_by == algorithm_type.value
        ]
        
        # If no relevant history, use all history
        if not relevant_history:
            relevant_history = suspicion_history
        
        # Calculate metrics
        observation_count = len(relevant_history)
        confirmed_count = sum(1 for s in relevant_history if s.approach_confirmed_suspicion)
        false_positive_count = sum(1 for s in relevant_history 
                                  if s.was_approached and not s.approach_confirmed_suspicion)
        
        confirmation_rate = confirmed_count / observation_count if observation_count > 0 else 0.0
        
        # Calculate last validation days
        last_validation = max([s.approached_at for s in relevant_history if s.approached_at], 
                             default=datetime.utcnow())
        last_validation_days = (datetime.utcnow() - last_validation).days
        
        # Calculate validation factor
        validation_factor = self.calculate_validation_factor(
            confirmation_rate, last_validation_days, observation_count
        )
        
        # Generate recommendation
        recommendation = self.generate_recommendation(
            confirmation_rate, validation_factor, last_validation_days
        )
        
        return ValidationContext(
            plate_number=plate_number,
            algorithm_type=algorithm_type,
            observation_count=observation_count,
            confirmed_count=confirmed_count,
            false_positive_count=false_positive_count,
            confirmation_rate=confirmation_rate,
            last_validation_days=last_validation_days,
            validation_factor=validation_factor,
            recommendation=recommendation
        )
    
    def calculate_validation_factor(
        self,
        confirmation_rate: float,
        last_validation_days: int,
        observation_count: int
    ) -> float:
        """
        Calculate validation factor based on confirmation history.
        
        Args:
            confirmation_rate: Rate of confirmed suspicions (0.0-1.0)
            last_validation_days: Days since last validation
            observation_count: Total observations
            
        Returns:
            Validation factor (0.0-2.0)
        """
        if observation_count < 3:
            # Insufficient data - neutral
            return 1.0
        
        # Base factor from confirmation rate
        if confirmation_rate >= 0.8:
            base_factor = 1.5  # Strong boost
        elif confirmation_rate >= 0.6:
            base_factor = 1.3  # Boost
        elif confirmation_rate >= 0.4:
            base_factor = 1.0  # Neutral
        elif confirmation_rate >= 0.2:
            base_factor = 0.7  # Penalty
        else:
            base_factor = 0.3  # Severe penalty
        
        # Time decay - older validations have less impact
        time_decay = 1.0
        if last_validation_days > 90:
            time_decay = 0.8
        elif last_validation_days > 180:
            time_decay = 0.6
        
        # Apply time decay
        final_factor = base_factor * time_decay
        
        # Clamp to reasonable range
        return max(0.1, min(2.0, final_factor))
    
    def generate_recommendation(
        self,
        confirmation_rate: float,
        validation_factor: float,
        last_validation_days: int
    ) -> str:
        """Generate human-readable recommendation."""
        if validation_factor >= 1.3:
            if last_validation_days < 30:
                return "High confirmation rate recent - boost algorithm result"
            else:
                return "Historically high confirmation rate - moderate boost"
        elif validation_factor <= 0.7:
            if last_validation_days < 30:
                return "Recent false positives - suppress algorithm result"
            else:
                return "Historically low confirmation rate - moderate penalty"
        else:
            return "Balanced confirmation rate - neutral adjustment"
    
    def determine_suppression(
        self,
        context: ValidationContext,
        original_result: any
    ) -> Tuple[bool, str]:
        """
        Determine if algorithm result should be suppressed.
        
        Args:
            context: Validation context
            original_result: Original algorithm result
            
        Returns:
            Tuple of (should_suppress, reason)
        """
        # Suppress if severe penalty
        if context.validation_factor <= 0.3:
            return True, f"Severe penalty factor ({context.validation_factor:.2f}) - too many false positives"
        
        # Suppress if low confirmation rate and recent validation
        if context.confirmation_rate < 0.2 and context.last_validation_days < 30:
            return True, f"Recent false positives ({context.false_positive_count} in last 30 days)"
        
        # Suppress if insufficient data
        if context.observation_count >= 3 and context.confirmation_rate < 0.1:
            return True, f"Consistently low confirmation rate ({context.confirmation_rate:.1%})"
        
        return False, "No suppression criteria met"
    
    async def record_feedback(
        self,
        db: AsyncSession,
        algorithm_type: AlgorithmType,
        observation_id: str,
        validation_factor: float,
        decision: str
    ) -> None:
        """
        Record feedback for algorithm learning.
        
        Args:
            db: Database session
            algorithm_type: Algorithm type
            observation_id: Observation ID
            validation_factor: Applied validation factor
            decision: Final decision (suppressed/adjusted/passed)
        """
        # Update algorithm run with validation metadata
        result = await db.execute(
            select(AlgorithmRun).where(
                and_(
                    AlgorithmRun.observation_id == observation_id,
                    AlgorithmRun.algorithm_type == algorithm_type
                )
            ).order_by(desc(AlgorithmRun.created_at)).limit(1)
        )
        
        run = result.scalar_one_or_none()
        
        if run:
            # Update output payload with validation info
            if run.output_payload is None:
                run.output_payload = {}
            
            run.output_payload.update({
                "validation_factor": validation_factor,
                "validation_decision": decision,
                "validation_timestamp": datetime.utcnow().isoformat()
            })
            
            await db.flush()
            
            logger.info(
                f"Recorded validation feedback for {algorithm_type.value} "
                f"on observation {observation_id}: factor={validation_factor:.2f}, decision={decision}"
            )
    
    async def get_algorithm_performance_with_validation(
        self,
        db: AsyncSession,
        algorithm_type: AlgorithmType,
        days: int = 30
    ) -> Dict:
        """
        Get algorithm performance metrics including validation impact.
        
        Args:
            db: Database session
            algorithm_type: Algorithm type
            days: Number of days to analyze
            
        Returns:
            Performance metrics with validation context
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get algorithm runs
        result = await db.execute(
            select(AlgorithmRun).where(
                and_(
                    AlgorithmRun.algorithm_type == algorithm_type,
                    AlgorithmRun.created_at >= start_date
                )
            )
        )
        runs = result.scalars().all()
        
        if not runs:
            return {
                "algorithm_type": algorithm_type.value,
                "total_runs": 0,
                "validation_adjusted": 0,
                "validation_suppressed": 0,
                "passed_through": 0,
                "avg_validation_factor": 0.0
            }
        
        # Analyze validation impact
        validation_adjusted = 0
        validation_suppressed = 0
        passed_through = 0
        validation_factors = []
        
        for run in runs:
            if run.output_payload:
                decision = run.output_payload.get("validation_decision")
                factor = run.output_payload.get("validation_factor", 1.0)
                validation_factors.append(factor)
                
                if decision == "suppressed":
                    validation_suppressed += 1
                elif decision == "adjusted":
                    validation_adjusted += 1
                else:
                    passed_through += 1
            else:
                passed_through += 1
                validation_factors.append(1.0)
        
        avg_validation_factor = sum(validation_factors) / len(validation_factors) if validation_factors else 1.0
        
        return {
            "algorithm_type": algorithm_type.value,
            "total_runs": len(runs),
            "validation_adjusted": validation_adjusted,
            "validation_suppressed": validation_suppressed,
            "passed_through": passed_through,
            "avg_validation_factor": avg_validation_factor,
            "adjustment_rate": validation_adjusted / len(runs) if runs else 0.0,
            "suppression_rate": validation_suppressed / len(runs) if runs else 0.0
        }
    
    async def get_validation_summary(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict:
        """
        Get summary of validation impact across all algorithms.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Validation summary
        """
        summary = {
            "period_days": days,
            "algorithms": {},
            "total_adjustments": 0,
            "total_suppressions": 0,
            "total_runs": 0
        }
        
        for algorithm_type in AlgorithmType:
            metrics = await self.get_algorithm_performance_with_validation(
                db, algorithm_type, days
            )
            summary["algorithms"][algorithm_type.value] = metrics
            summary["total_adjustments"] += metrics["validation_adjusted"]
            summary["total_suppressions"] += metrics["validation_suppressed"]
            summary["total_runs"] += metrics["total_runs"]
        
        return summary


# Global service instance
algorithm_validation_service = AlgorithmValidationService()
