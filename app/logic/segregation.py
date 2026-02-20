from typing import Set

class SegregationEngine:
    """ IATA Segregation Rules (Simplified) """
    CONFLICTS = {
        "RXB": ["GEN", "RCX", "RFL"], 
        "AVI": ["RRY", "ICE", "HUM"], 
        "HUM": ["EAT", "PES"],
        "EAT": ["HUM", "RPB", "RIS"]
    }
    
    @staticmethod
    def check_mix(existing: Set[str], new_shc: str) -> bool:
        # Check if new SHC conflicts with existing
        if new_shc in SegregationEngine.CONFLICTS:
            for bad in SegregationEngine.CONFLICTS[new_shc]:
                if bad in existing: return False
        
        # Check if existing SHC conflicts with new
        for exist in existing:
            if exist in SegregationEngine.CONFLICTS:
                if new_shc in SegregationEngine.CONFLICTS[exist]: return False
        return True