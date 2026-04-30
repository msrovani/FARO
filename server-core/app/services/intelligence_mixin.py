from abc import ABC, abstractmethod
from app.schemas.decision_log import DecisionLogSchema

class IntelligenceMixin(ABC):
    @abstractmethod
    def generate_decision_log(self, decision_id: str, score: float, factors: List[Dict[str, Any]], version: str) -> DecisionLogSchema:
        """Helper to standardize decision logging across intelligence services."""
        pass
