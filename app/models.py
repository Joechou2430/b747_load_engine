# app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- PHASE 1 & 6: Data Models with Revenue Integration ---

class Position(BaseModel):
    name: str
    zone: str
    deck: str  # 'MAIN' or 'LOWER'
    start_station: float
    end_station: float
    centroid_arm: float
    max_weight: float
    # New in Phase 6: Baseline value for displacement cost calculation
    baseline_value: float = Field(default=0.0, description="Historical or expected revenue value of this position")

class CargoItem(BaseModel):
    id: str
    uld_type: str  # e.g., 'M', 'R', 'G', 'AKE'
    weight: float
    volume: float
    # New in Phase 6: Revenue data for RMS
    revenue: float = Field(default=0.0, description="Total expected revenue for this cargo")
    is_dgr: bool = False
    dgr_code: Optional[str] = None

class LoadPlanItem(BaseModel):
    cargo: CargoItem
    position_name: str

class LoadPlan(BaseModel):
    items: List[LoadPlanItem]
    total_weight: float = 0.0
    total_revenue: float = 0.0
    cg_station: float = 0.0
    mac_percent: float = 0.0

class DisplacementResult(BaseModel):
    cargo_id: str
    target_position: str
    blocked_positions: List[str]
    displacement_cost: float
    net_profit: float
    is_profitable: bool
    is_loadable: bool
    rejection_reason: Optional[str] = None