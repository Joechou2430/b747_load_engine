import math
from typing import Dict, Tuple, Optional
from ..models import CargoRequest
from ..config import ULDLibrary, SystemConfig, AircraftMap

class ShoringEngine:
    """ Feature 1: 墊板計算、板型推薦、合法凸盤判斷 """
    
    @staticmethod
    def calculate_shoring_needs(cargo: CargoRequest, uld_type: str, arm: float = 0) -> Dict:
        res = {"needed": False, "weight": 0.0, "height": 0.0, "reasons": []}
        if not cargo.dims: return res
        
        dim = max(cargo.dims, key=lambda d: d['l']*d['w'])
        c_len, c_wid = dim['l'], dim['w']
        c_wgt = cargo.weight / cargo.pieces
        
        # A. Area Load Check
        area_m2 = (c_len * c_wid) / 10000.0
        pressure = c_wgt / area_m2 if area_m2 else 99999
        if pressure > SystemConfig.FLOOR_LIMIT_KG_M2:
            spec = ULDLibrary.SPECS.get(uld_type)
            if spec:
                full_base_m2 = (spec['len']*2.54 * spec['wid']*2.54) / 10000
                w_cost = full_base_m2 * 0.02 * SystemConfig.SHORING_DENSITY # 2cm thick
                res["needed"] = True; res["weight"] += w_cost; res["height"] += 2.0
                res["reasons"].append(f"Area Load ({pressure:.0f} > {SystemConfig.FLOOR_LIMIT_KG_M2})")

        # B. Linear Load Check
        limit_linear = AircraftMap.get_linear_limit(arm)
        actual_linear = c_wgt / (c_len / 2.54)
        if actual_linear > limit_linear:
            req_len_in = c_wgt / limit_linear
            req_len_cm = req_len_in * 2.54
            vol_m3 = 3 * 0.1 * (req_len_cm / 100.0) * 0.1 
            w_cost = vol_m3 * SystemConfig.SHORING_DENSITY
            res["needed"] = True; res["weight"] += w_cost; res["height"] += 10.0
            res["reasons"].append(f"Linear Load ({actual_linear:.1f} > {limit_linear})")

        # C. Contour Overhang Check
        if "LOWER" in uld_type and c_wid > 244:
            overhang = (c_wid - 244) / 2
            req_h = overhang / 1.5 + 5.0 
            
            if req_h > res["height"]:
                diff = req_h - res["height"]
                vol_m3 = area_m2 * (diff / 100.0)
                w_cost = vol_m3 * SystemConfig.SHORING_DENSITY
                res["weight"] += w_cost
                res["height"] = req_h
                res["reasons"].append(f"Contour Overhang ({overhang:.1f}cm)")
                
        return res

    @staticmethod
    def recommend_type(cargo: CargoRequest) -> Dict:
        # 注意：這裡假設 cargo 已經被拆分為單件 (pieces=1)
        weight = cargo.weight 
        
        lim_m = ULDLibrary.SPECS["M"]["max_gross"]
        lim_r = ULDLibrary.SPECS["R"]["max_gross"]
        lim_g = ULDLibrary.SPECS["G"]["max_gross"]
        
        # 1. Lower Deck Check
        if 0 < cargo.max_height <= 163:
            if weight < 1500 and cargo.volume < 4.0:
                return {"type": "K", "contour": "LD3", "reason": "Lower Container", "floating": False}
            else:
                return {"type": "M_LOWER", "contour": "LOWER", "reason": "Lower Pallet", "floating": False}

        # 2. Main Deck Weight Check (包含 Floating Load 邏輯)
        if weight > lim_g: 
            # 超過 20ft 極限，改用 Floating Load 邏輯
            return {"type": "G", "contour": "FLAT", "reason": "Floating Load (Requires Aircraft Tie-down)", "floating": True}
        if weight > lim_r: 
            return {"type": "G", "contour": "FLAT", "reason": "20ft", "floating": False}
        if weight > lim_m: 
            return {"type": "R", "contour": "FLAT", "reason": "16ft", "floating": False}
        
        return {"type": "M", "contour": "Q6", "reason": "Standard", "floating": False}