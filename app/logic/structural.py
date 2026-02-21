from typing import Tuple, List
from ..models import PackedULD
from ..config import ULDLibrary, AircraftMap

class StructuralEngine:
    """ Feature 3: Structural Integrity Checks """

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

    @staticmethod
    def check_zone_limits(packed_ulds: List[PackedULD]) -> List[str]:
        """ 
        Verifies if total weight in specific zones exceeds limits.
        """
        warnings = []
        zone_weights = {z: 0.0 for z in AircraftMap.ZONE_LIMITS.keys()}
        
        for uld in packed_ulds:
            if not uld.assigned_position or uld.assigned_position == "UNASSIGNED":
                continue
                
            arm = uld.assigned_arm
            weight = uld.gross_weight
            
            # Check which zone this ULD falls into
            for z_name, limit_info in AircraftMap.ZONE_LIMITS.items():
                if limit_info["start"] <= arm <= limit_info["end"]:
                    zone_weights[z_name] += weight
        
        # Check against limits
        for z_name, current_w in zone_weights.items():
            limit = AircraftMap.ZONE_LIMITS[z_name]["limit"]
            if current_w > limit:
                warnings.append(f"Zone {z_name} Overweight! {current_w:.0f} > Limit {limit}")
                
        return warnings