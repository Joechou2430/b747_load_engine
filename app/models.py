from dataclasses import dataclass, field
from typing import List, Optional, Set
from .config import ULDLibrary

@dataclass
class CargoRequest:
    id: str
    destination: str
    weight: float
    volume: float
    pieces: int
    dims: List[dict] = field(default_factory=list)
    shc: List[str] = field(default_factory=list)
    assigned_uld_type: Optional[str] = None

    @property
    def max_height(self):
        if not self.dims: return 0
        return max([d.get('h', 0) for d in self.dims])

@dataclass
class PackedULD:
    id: str
    uld_type: str
    contour: str
    destination: str
    items: List[CargoRequest] = field(default_factory=list)
    total_weight: float = 0.0
    total_volume: float = 0.0
    is_pure: bool = False
    status: str = "OPEN"
    shc_codes: Set[str] = field(default_factory=set)
    assigned_position: Optional[str] = None
    assigned_arm: float = 0.0
    
    # Shoring Info
    shoring_weight: float = 0.0
    shoring_note: str = ""

    @property
    def gross_weight(self):
        spec = ULDLibrary.SPECS.get(self.uld_type)
        tare = spec['tare'] if spec else 0
        return self.total_weight + tare + self.shoring_weight

    @property
    def utilization_pct(self):
        spec = ULDLibrary.SPECS.get(self.uld_type)
        return (self.total_volume / spec['max_vol']) * 100 if spec else 0