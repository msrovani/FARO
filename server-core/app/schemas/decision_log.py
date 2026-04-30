from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class DecisionFactor(BaseModel):
    factor_name: str
    weight: float
    description: str

class DecisionLogSchema(BaseModel):
    decision_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_score: float
    factors: List[DecisionFactor]
    model_version: str
    metadata: Optional[Dict[str, Any]] = None
