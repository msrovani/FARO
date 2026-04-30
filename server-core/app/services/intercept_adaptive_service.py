"""
F.A.R.O. INTERCEPT Adaptive Service
Adaptive weights and learning for INTERCEPT algorithm.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from app.db.base import InterceptEvent, VehicleObservation, AlgorithmRun
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class AlgorithmType(Enum):
    """Algorithm types for INTERCEPT."""
    WATCHLIST = "watchlist"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    ROUTE_ANOMALY = "route_anomaly"
    SENSITIVE_ZONE = "sensitive_zone"
    CONVOY = "convoy"
    ROAMING = "roaming"


@dataclass
class InterceptWeights:
    """INTERCEPT algorithm weights."""
    watchlist: float = 0.35
    impossible_travel: float = 0.25
    route_anomaly: float = 0.15
    sensitive_zone: float = 0.10
    convoy: float = 0.10
    roaming: float = 0.05
    
    def validate(self) -> bool:
        """Validate weights sum to 1.0."""
        total = sum([
            self.watchlist, self.impossible_travel, self.route_anomaly,
            self.sensitive_zone, self.convoy, self.roaming
        ])
        return abs(total - 1.0) < 0.001


@dataclass
class PerformanceMetrics:
    """Algorithm performance metrics."""
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    avg_confidence: float = 0.0
    avg_execution_time_ms: float = 0.0
    
    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        """F1 Score = 2 * (precision * recall) / (precision + recall)"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


class InterceptAdaptiveService:
    """Adaptive INTERCEPT algorithm service with learning capabilities."""
    
    def __init__(self):
        self.default_weights = InterceptWeights()
        self.cache_ttl = timedelta(hours=1)
        
    async def get_adaptive_weights(
        self,
        db: AsyncSession,
        context: Optional[Dict] = None
    ) -> InterceptWeights:
        """
        Get adaptive weights based on context and performance.
        
        Args:
            db: Database session
            context: Context information (time, location, etc.)
            
        Returns:
            Adaptive weights for INTERCEPT algorithm
        """
        # Try cache first
        cache_key = "intercept:adaptive_weights"
        cached_weights = await cache_service.get(cache_key)
        if cached_weights:
            return InterceptWeights(**cached_weights)
        
        # Calculate adaptive weights based on performance
        performance = await self.calculate_algorithm_performance(db)
        adaptive_weights = self.calculate_adaptive_weights(performance)
        
        # Cache the result
        await cache_service.set(cache_key, adaptive_weights.__dict__, self.cache_ttl)
        
        return adaptive_weights
    
    async def calculate_algorithm_performance(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[AlgorithmType, PerformanceMetrics]:
        """
        Calculate performance metrics for each algorithm.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Performance metrics by algorithm type
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        performance = {}
        
        for algorithm_type in AlgorithmType:
            metrics = await self.calculate_algorithm_metrics(db, algorithm_type, start_date)
            performance[algorithm_type] = metrics
        
        return performance
    
    async def calculate_algorithm_metrics(
        self,
        db: AsyncSession,
        algorithm_type: AlgorithmType,
        start_date: datetime
    ) -> PerformanceMetrics:
        """
        Calculate metrics for a specific algorithm.
        
        Args:
            db: Database session
            algorithm_type: Algorithm type to analyze
            start_date: Start date for analysis
            
        Returns:
            Performance metrics
        """
        # Get algorithm runs in the period
        result = await db.execute(
            select(AlgorithmRun)
            .where(
                and_(
                    AlgorithmRun.algorithm_type == algorithm_type.value,
                    AlgorithmRun.created_at >= start_date
                )
            )
            .order_by(desc(AlgorithmRun.created_at))
        )
        runs = result.scalars().all()
        
        if not runs:
            return PerformanceMetrics()
        
        # Calculate metrics
        metrics = PerformanceMetrics()
        execution_times = []
        confidences = []
        
        for run in runs:
            execution_times.append(run.duration_seconds * 1000)  # Convert to ms
            confidences.append(run.outcome.confidence)
            
            # Count outcomes (simplified - in real implementation would track actual TP/FP/etc.)
            if run.outcome.decision.value in ["critical_match", "relevant_match", "strong_match"]:
                metrics.true_positives += 1
            elif run.outcome.decision.value == "no_match":
                metrics.true_negatives += 1
            else:
                # This would need more sophisticated tracking in real implementation
                metrics.false_positives += 1 if run.outcome.confidence > 0.7 else 0
                metrics.false_negatives += 1 if run.outcome.confidence < 0.3 else 0
        
        # Calculate averages
        if execution_times:
            metrics.avg_execution_time_ms = sum(execution_times) / len(execution_times)
        if confidences:
            metrics.avg_confidence = sum(confidences) / len(confidences)
        
        return metrics
    
    def calculate_adaptive_weights(
        self,
        performance: Dict[AlgorithmType, PerformanceMetrics]
    ) -> InterceptWeights:
        """
        Calculate adaptive weights based on algorithm performance.
        
        Args:
            performance: Performance metrics by algorithm
            
        Returns:
            Adaptive weights
        """
        weights = InterceptWeights()
        
        # Weight adjustments based on performance
        adjustments = {
            AlgorithmType.WATCHLIST: self.calculate_weight_adjustment(performance[AlgorithmType.WATCHLIST]),
            AlgorithmType.IMPOSSIBLE_TRAVEL: self.calculate_weight_adjustment(performance[AlgorithmType.IMPOSSIBLE_TRAVEL]),
            AlgorithmType.ROUTE_ANOMALY: self.calculate_weight_adjustment(performance[AlgorithmType.ROUTE_ANOMALY]),
            AlgorithmType.SENSITIVE_ZONE: self.calculate_weight_adjustment(performance[AlgorithmType.SENSITIVE_ZONE]),
            AlgorithmType.CONVOY: self.calculate_weight_adjustment(performance[AlgorithmType.CONVOY]),
            AlgorithmType.ROAMING: self.calculate_weight_adjustment(performance[AlgorithmType.ROAMING])
        }
        
        # Apply adjustments
        weights.watchlist = max(0.05, min(0.60, self.default_weights.watchlist * adjustments[AlgorithmType.WATCHLIST]))
        weights.impossible_travel = max(0.05, min(0.50, self.default_weights.impossible_travel * adjustments[AlgorithmType.IMPOSSIBLE_TRAVEL]))
        weights.route_anomaly = max(0.05, min(0.30, self.default_weights.route_anomaly * adjustments[AlgorithmType.ROUTE_ANOMALY]))
        weights.sensitive_zone = max(0.05, min(0.25, self.default_weights.sensitive_zone * adjustments[AlgorithmType.SENSITIVE_ZONE]))
        weights.convoy = max(0.05, min(0.25, self.default_weights.convoy * adjustments[AlgorithmType.CONVOY]))
        weights.roaming = max(0.01, min(0.20, self.default_weights.roaming * adjustments[AlgorithmType.ROAMING]))
        
        # Normalize to sum to 1.0
        total = sum([
            weights.watchlist, weights.impossible_travel, weights.route_anomaly,
            weights.sensitive_zone, weights.convoy, weights.roaming
        ])
        
        if total > 0:
            weights.watchlist /= total
            weights.impossible_travel /= total
            weights.route_anomaly /= total
            weights.sensitive_zone /= total
            weights.convoy /= total
            weights.roaming /= total
        
        logger.info(f"Adaptive weights calculated: {weights}")
        return weights
    
    def calculate_weight_adjustment(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate weight adjustment based on performance metrics.
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Weight adjustment factor (1.0 = no adjustment)
        """
        if metrics.true_positives + metrics.false_positives == 0:
            return 1.0  # No data, no adjustment
        
        # Base adjustment on F1 score
        f1 = metrics.f1_score
        
        # Adjust based on execution time (slower algorithms get slight penalty)
        time_penalty = 1.0
        if metrics.avg_execution_time_ms > 200:  # > 200ms
            time_penalty = 0.95
        elif metrics.avg_execution_time_ms > 100:  # > 100ms
            time_penalty = 0.98
        
        # Calculate final adjustment
        if f1 > 0.8:
            adjustment = 1.1  # Boost high-performing algorithms
        elif f1 > 0.6:
            adjustment = 1.0  # Keep default for good performance
        elif f1 > 0.4:
            adjustment = 0.9  # Slight penalty for moderate performance
        else:
            adjustment = 0.8  # Reduce weight for poor performance
        
        return adjustment * time_penalty
    
    async def record_intercept_feedback(
        self,
        db: AsyncSession,
        intercept_event_id: str,
        feedback: Dict
    ) -> bool:
        """
        Record operator feedback for INTERCEPT events.
        
        Args:
            db: Database session
            intercept_event_id: INTERCEPT event ID
            feedback: Feedback data (correct, recommendation, etc.)
            
        Returns:
            Success status
        """
        try:
            # Store feedback (would need a feedback table in real implementation)
            feedback_data = {
                "intercept_event_id": intercept_event_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache feedback for learning
            cache_key = f"intercept:feedback:{intercept_event_id}"
            await cache_service.set(cache_key, feedback_data, timedelta(days=30))
            
            # Invalidate weights cache to trigger recalculation
            await cache_service.invalidate_pattern("intercept:adaptive_weights")
            
            logger.info(f"Recorded feedback for INTERCEPT event {intercept_event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording INTERCEPT feedback: {e}")
            return False
    
    async def get_intercept_analytics(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict:
        """
        Get comprehensive INTERCEPT analytics.
        
        Args:
            db: Database session
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get INTERCEPT events
        result = await db.execute(
            select(InterceptEvent)
            .where(InterceptEvent.created_at >= start_date)
            .order_by(desc(InterceptEvent.created_at))
        )
        events = result.scalars().all()
        
        if not events:
            return {
                "total_events": 0,
                "avg_score": 0.0,
                "recommendations": {},
                "performance": {}
            }
        
        # Calculate analytics
        total_events = len(events)
        avg_score = sum(event.intercept_score for event in events) / total_events
        
        # Count recommendations
        recommendations = {}
        for event in events:
            rec = event.recommendation
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        # Get current weights
        current_weights = await self.get_adaptive_weights(db)
        
        # Get algorithm performance
        performance = await self.calculate_algorithm_performance(db, days)
        
        return {
            "total_events": total_events,
            "avg_score": avg_score,
            "recommendations": recommendations,
            "current_weights": current_weights.__dict__,
            "algorithm_performance": {
                alg_type.value: {
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score,
                    "avg_execution_time_ms": metrics.avg_execution_time_ms
                }
                for alg_type, metrics in performance.items()
            },
            "period_days": days
        }
    
    async def optimize_weights_for_context(
        self,
        db: AsyncSession,
        context: Dict
    ) -> InterceptWeights:
        """
        Optimize weights for specific context.
        
        Args:
            db: Database session
            context: Context (time, location, vehicle_type, etc.)
            
        Returns:
            Context-optimized weights
        """
        # Get base adaptive weights
        base_weights = await self.get_adaptive_weights(db, context)
        
        # Context-specific adjustments
        weights = InterceptWeights(**base_weights.__dict__)
        
        # Time-based adjustments
        hour = context.get("hour", datetime.utcnow().hour)
        if 22 <= hour or hour <= 5:  # Night time
            # Increase weight for impossible travel (more suspicious at night)
            weights.impossible_travel = min(0.40, weights.impossible_travel * 1.2)
            # Decrease weight for route anomaly (less traffic data at night)
            weights.route_anomaly = max(0.05, weights.route_anomaly * 0.8)
        
        # Location-based adjustments
        location_type = context.get("location_type", "urban")
        if location_type == "highway":
            # Increase convoy detection on highways
            weights.convoy = min(0.25, weights.convoy * 1.3)
            # Decrease sensitive zone (fewer zones on highways)
            weights.sensitive_zone = max(0.05, weights.sensitive_zone * 0.7)
        elif location_type == "urban":
            # Increase sensitive zone in urban areas
            weights.sensitive_zone = min(0.20, weights.sensitive_zone * 1.2)
            # Decrease convoy (less relevant in cities)
            weights.convoy = max(0.05, weights.convoy * 0.8)
        
        # Vehicle type adjustments
        vehicle_type = context.get("vehicle_type", "unknown")
        if vehicle_type == "motorcycle":
            # Increase impossible travel (motorcycles can travel faster)
            weights.impossible_travel = min(0.35, weights.impossible_travel * 1.1)
        elif vehicle_type == "truck":
            # Decrease impossible travel (trucks travel slower)
            weights.impossible_travel = max(0.15, weights.impossible_travel * 0.8)
            # Increase route anomaly (trucks have specific routes)
            weights.route_anomaly = min(0.20, weights.route_anomaly * 1.2)
        
        # Normalize weights
        total = sum([
            weights.watchlist, weights.impossible_travel, weights.route_anomaly,
            weights.sensitive_zone, weights.convoy, weights.roaming
        ])
        
        if total > 0:
            weights.watchlist /= total
            weights.impossible_travel /= total
            weights.route_anomaly /= total
            weights.sensitive_zone /= total
            weights.convoy /= total
            weights.roaming /= total
        
        logger.info(f"Context-optimized weights for {context}: {weights}")
        return weights


# Global service instance
intercept_adaptive_service = InterceptAdaptiveService()
