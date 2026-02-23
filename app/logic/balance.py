from typing import List, Dict
from dataclasses import dataclass
from ..models import PackedULD

@dataclass
class AircraftWeightConfig:
    """ Aircraft Basic Weight Parameters """
    dow: float       # Dry Operating Weight (kg)
    doi: float       # Dry Operating Index
    mac_len: float   # Mean Aerodynamic Chord Length (inches)
    lemac: float     # Leading Edge of MAC (inches)

@dataclass
class EnvelopeLimits:
    """ CG Envelope Limits (% MAC) """
    fwd_limit: float
    aft_limit: float

class WeightBalanceEngine:
    """
    Calculates Center of Gravity (CG) and checks against envelope limits.
    """

    @staticmethod
    def calculate_cg(
        ac_config: AircraftWeightConfig, 
        packed_ulds: List[PackedULD]
    ) -> Dict:
        """
        Calculates Zero Fuel Weight (ZFW) CG.
        """
        # 1. Base State (DOW)
        # Assuming DOW CG starts at approx 25% MAC for calculation base
        dow_arm = ac_config.lemac + (ac_config.mac_len * 0.25)
        total_moment = ac_config.dow * dow_arm
        total_weight = ac_config.dow
        
        payload_weight = 0.0
        payload_moment = 0.0

        # 2. Add Payload
        for uld in packed_ulds:
            if not uld.assigned_position or uld.assigned_position == "UNASSIGNED":
                continue
            
            w = uld.gross_weight
            arm = uld.assigned_arm # Centroid from AircraftMap
            
            m = w * arm
            
            payload_weight += w
            payload_moment += m
            total_weight += w
            total_moment += m

        # 3. Calculate Final CG Arm
        final_cg_arm = total_moment / total_weight if total_weight > 0 else 0
        
        # 4. Convert to % MAC
        # Formula: %MAC = (CG - LEMAC) / MAC * 100
        cg_mac_percent = ((final_cg_arm - ac_config.lemac) / ac_config.mac_len) * 100

        return {
            "zfw_kg": round(total_weight, 1),
            "payload_kg": round(payload_weight, 1),
            "total_moment": round(total_moment, 1),
            "cg_arm_in": round(final_cg_arm, 1),
            "cg_mac_pct": round(cg_mac_percent, 2)
        }

    @staticmethod
    def validate_envelope(cg_mac: float, limits: EnvelopeLimits) -> Dict:
        """ Checks if CG is within safe limits """
        if cg_mac < limits.fwd_limit:
            return {
                "status": "FAIL", 
                "msg": f"NOSE HEAVY! CG {cg_mac}% < Fwd Limit {limits.fwd_limit}%"
            }
        
        if cg_mac > limits.aft_limit:
            return {
                "status": "FAIL", 
                "msg": f"TAIL HEAVY! CG {cg_mac}% > Aft Limit {limits.aft_limit}%"
            }
            
        return {"status": "OK", "msg": "Within Envelope"}