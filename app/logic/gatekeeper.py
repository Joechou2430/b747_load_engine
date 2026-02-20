from typing import Dict
from ..models import CargoRequest
from ..config import DoorLimits

class Gatekeeper:
    """
    Validates if cargo dimensions fit through aircraft doors.
    """
    
    @staticmethod
    def validate_door_entry(cargo: CargoRequest) -> Dict:
        """
        Checks if cargo fits through any door.
        Returns: {"pass": bool, "entry_point": str, "reason": str}
        """
        if not cargo.dims:
            return {"pass": True, "entry_point": "Loose", "reason": "No dims provided"}

        # Assume worst case: single largest piece needs to fit
        piece = max(cargo.dims, key=lambda d: d['l']*d['w']*d['h'])
        # Get 2 smallest dimensions (since cargo can be rotated)
        dims = sorted([piece['l'], piece['w'], piece['h']]) 
        min_dim = dims[0]
        mid_dim = dims[1]
        
        # 1. Lower Deck Door Check
        if mid_dim <= DoorLimits.LOWER_DOOR["max_h"] and min_dim <= DoorLimits.LOWER_DOOR["max_w"]:
             return {"pass": True, "entry_point": "Lower", "reason": "Fits Lower Door"}

        # 2. Main Deck Side Cargo Door (SCD) Check
        if mid_dim <= DoorLimits.SIDE_DOOR["max_h"] and min_dim <= DoorLimits.SIDE_DOOR["max_w"]:
            return {"pass": True, "entry_point": "Main-SCD", "reason": "Fits Main Side Door"}

        # 3. Main Deck Nose Door Check
        if mid_dim <= DoorLimits.NOSE_DOOR["max_h"] and min_dim <= DoorLimits.NOSE_DOOR["max_w"]:
            return {"pass": True, "entry_point": "Main-Nose", "reason": "Fits Nose Door"}

        return {
            "pass": False, 
            "entry_point": "None", 
            "reason": f"Dims {int(min_dim)}x{int(mid_dim)}cm exceed all doors."
        }