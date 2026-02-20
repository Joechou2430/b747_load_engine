from typing import Tuple
from ..models import PackedULD
from ..config import ULDLibrary, AircraftMap

class StructuralEngine:
    @staticmethod
    def check_linear_load(uld: PackedULD, arm: float) -> Tuple[bool, str]:
        spec = ULDLibrary.SPECS.get(uld.uld_type)
        if not spec: return False, "Unknown ULD"
        
        limit = AircraftMap.get_linear_limit(arm)
        # Linear Load = Gross Weight / Length along fuselage
        linear_load = uld.gross_weight / spec['len']
        
        if linear_load > limit:
            return False, f"Load {linear_load:.1f} kg/in > Limit {limit} kg/in"
        return True, "OK"