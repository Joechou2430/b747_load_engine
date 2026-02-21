from typing import Dict, List, Tuple

class SystemConfig:
    PACKING_LOSS_FACTOR = 0.85
    SHORING_DENSITY = 600.0     # kg/m3
    FLOOR_LIMIT_KG_M2 = 976.0   # kg/m2

class DoorLimits:
    """ Cargo Door Dimensions (cm) """
    NOSE_DOOR = {"max_h": 244.0, "max_w": 269.0, "name": "Nose Door"}
    SIDE_DOOR = {"max_h": 305.0, "max_w": 340.0, "name": "Side Cargo Door"}
    LOWER_DOOR = {"max_h": 167.0, "max_w": 264.0, "name": "Lower Deck Door"}
    BULK_DOOR = {"max_h": 111.0, "max_w": 119.0, "name": "Bulk Door"}

class ULDLibrary:
    """ B747-400F ULD Specifications """
    SPECS = {
        "M":      {"code": "PMC-Q6", "contour": "Q6",    "max_gross": 6804.0,  "tare": 120.0, "max_vol": 19.0, "len": 125, "wid": 96},
        "M_Q7":   {"code": "PMC-Q7", "contour": "Q7",    "max_gross": 6804.0,  "tare": 120.0, "max_vol": 24.0, "len": 125, "wid": 96},
        "A":      {"code": "PAG",    "contour": "Q6",    "max_gross": 6033.0,  "tare": 110.0, "max_vol": 17.0, "len": 125, "wid": 88},
        "R":      {"code": "PRA",    "contour": "FLAT",  "max_gross": 11340.0, "tare": 400.0, "max_vol": 27.0, "len": 196, "wid": 96},
        "G":      {"code": "PGA",    "contour": "FLAT",  "max_gross": 13608.0, "tare": 500.0, "max_vol": 33.0, "len": 238.5,"wid": 96},
        "K":      {"code": "AKE",    "contour": "LD3",   "max_gross": 1587.0,  "tare": 90.0,  "max_vol": 4.3,  "len": 61.5, "wid": 60.4},
        "M_LOWER":{"code": "PMC-LD", "contour": "LOWER", "max_gross": 5035.0,  "tare": 120.0, "max_vol": 11.5, "len": 125, "wid": 96},
        "A_LOWER":{"code": "PAG-LD", "contour": "LOWER", "max_gross": 4626.0,  "tare": 110.0, "max_vol": 10.5, "len": 125, "wid": 88}
    }

class AircraftMap:
    """ 
    B747-400F Positions & Interlocks
    """
    
    # Main Deck Centroids (Inches)
    CENTROIDS = {
        "A": 320.0, "B": 453.0, "C": 588.0, "D": 714.0, "E": 840.0,
        "F": 966.0, "G": 1092.0, "H": 1218.0, "J": 1344.0, "K": 1470.0,
        "L": 1596.0, "M": 1722.0, "P": 1848.0, "Q": 1939.0, "R": 2029.0,
        "S": 2155.0, "T": 2296.0
    }

    # Main Deck Positions
    MAIN_POSITIONS = {
        "A1": {"deck": "Main", "type": "Center", "arm": 320.0, "conflicts": []},
        "A2": {"deck": "Main", "type": "Center", "arm": 379.0, "conflicts": []},
        "B":  {"deck": "Main", "type": "Center", "arm": 453.0, "conflicts": []},
        "T":  {"deck": "Main", "type": "Center", "arm": 2296.0, "conflicts": []},
    }
    
    ROW_ZONES = ["C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "P", "Q", "R", "S"]

    # Lower Deck Positions
    LOWER_POSITIONS = {
        "11P": {"deck": "Lower", "type": "Center", "arm": 513.2, "conflicts": ["11L", "11R"]},
        "11L": {"deck": "Lower", "type": "Left",   "arm": 510.4, "conflicts": ["11P"]},
        "11R": {"deck": "Lower", "type": "Right",  "arm": 510.4, "conflicts": ["11P"]},
        "12P": {"deck": "Lower", "type": "Center", "arm": 610.2, "conflicts": ["12L", "12R", "13L", "13R"]},
        "12L": {"deck": "Lower", "type": "Left",   "arm": 571.6, "conflicts": ["12P"]},
        "12R": {"deck": "Lower", "type": "Right",  "arm": 571.6, "conflicts": ["12P"]},
        "13L": {"deck": "Lower", "type": "Left",   "arm": 632.9, "conflicts": ["12P"]},
        "13R": {"deck": "Lower", "type": "Right",  "arm": 632.9, "conflicts": ["12P"]},
        "21P": {"deck": "Lower", "type": "Center", "arm": 744.7, "conflicts": ["21L", "21R", "22L", "22R"]},
        "21L": {"deck": "Lower", "type": "Left",   "arm": 713.9, "conflicts": ["21P"]},
        "21R": {"deck": "Lower", "type": "Right",  "arm": 713.9, "conflicts": ["21P"]},
        "22L": {"deck": "Lower", "type": "Left",   "arm": 774.4, "conflicts": ["21P"]},
        "22R": {"deck": "Lower", "type": "Right",  "arm": 774.4, "conflicts": ["21P"]},
        "22P": {"deck": "Lower", "type": "Center", "arm": 841.7, "conflicts": ["23L", "23R"]},
        "23L": {"deck": "Lower", "type": "Left",   "arm": 834.9, "conflicts": ["22P"]},
        "23R": {"deck": "Lower", "type": "Right",  "arm": 834.9, "conflicts": ["22P"]},
        "23P": {"deck": "Lower", "type": "Center", "arm": 938.7, "conflicts": ["24L", "24R", "25L", "25R"]},
        "24L": {"deck": "Lower", "type": "Left",   "arm": 895.4, "conflicts": ["23P"]},
        "24R": {"deck": "Lower", "type": "Right",  "arm": 895.4, "conflicts": ["23P"]},
        "25L": {"deck": "Lower", "type": "Left",   "arm": 956.4, "conflicts": ["23P"]},
        "25R": {"deck": "Lower", "type": "Right",  "arm": 956.4, "conflicts": ["23P"]},
        "31P": {"deck": "Lower", "type": "Center", "arm": 1534.6, "conflicts": ["31L", "31R", "32L", "32R"]},
        "31L": {"deck": "Lower", "type": "Left",   "arm": 1517.0, "conflicts": ["31P"]},
        "31R": {"deck": "Lower", "type": "Right",  "arm": 1517.0, "conflicts": ["31P"]},
        "32L": {"deck": "Lower", "type": "Left",   "arm": 1577.4, "conflicts": ["31P"]},
        "32R": {"deck": "Lower", "type": "Right",  "arm": 1577.4, "conflicts": ["31P"]},
        "32P": {"deck": "Lower", "type": "Center", "arm": 1631.6, "conflicts": ["33L", "33R"]},
        "33L": {"deck": "Lower", "type": "Left",   "arm": 1637.9, "conflicts": ["32P"]},
        "33R": {"deck": "Lower", "type": "Right",  "arm": 1637.9, "conflicts": ["32P"]},
        "41P": {"deck": "Lower", "type": "Center", "arm": 1728.6, "conflicts": ["41L", "41R", "42L", "42R"]},
        "41L": {"deck": "Lower", "type": "Left",   "arm": 1698.4, "conflicts": ["41P"]},
        "41R": {"deck": "Lower", "type": "Right",  "arm": 1698.4, "conflicts": ["41P"]},
        "42L": {"deck": "Lower", "type": "Left",   "arm": 1758.9, "conflicts": ["41P"]},
        "42R": {"deck": "Lower", "type": "Right",  "arm": 1758.9, "conflicts": ["41P"]},
        "42P": {"deck": "Lower", "type": "Center", "arm": 1825.6, "conflicts": ["43L", "43R"]},
        "43L": {"deck": "Lower", "type": "Left",   "arm": 1820.6, "conflicts": ["42P"]},
        "43R": {"deck": "Lower", "type": "Right",  "arm": 1820.6, "conflicts": ["42P"]},
        "44L": {"deck": "Lower", "type": "Left",   "arm": 1882.4, "conflicts": []},
        "44R": {"deck": "Lower", "type": "Right",  "arm": 1882.4, "conflicts": []},
        "45L": {"deck": "Lower", "type": "Left",   "arm": 1944.2, "conflicts": []},
        "45R": {"deck": "Lower", "type": "Right",  "arm": 1944.2, "conflicts": []},
    }

    # Linear Load Limits (Start Arm, End Arm, Limit)
    LINEAR_LIMITS = [
        (0, 525, 38.5), (525, 1000, 77.1), (1000, 1480, 131.5), 
        (1480, 1920, 77.1), (1920, 2500, 16.3)
    ]

    # Cumulative Zone Limits (Pivot Weights)
    # Source: Figure 33.1.18
    ZONE_LIMITS = {
        "FWD_LOWER": {"start": 360, "end": 1000, "limit": 27669},
        "AFT_LOWER": {"start": 1480, "end": 1900, "limit": 26081},
        "BULK":      {"start": 1900, "end": 2160, "limit": 4408},
        "WINGBOX":   {"start": 1000, "end": 1480, "limit": 45000} # Estimated limit for Main Deck center
    }

    # Disabled Positions
    DISABLED_POSITIONS = set()

    @classmethod
    def initialize_maps(cls):
        # 1. Build Main Deck Positions
        cls.MAIN_POSITIONS = {
            "A1": {"deck": "Main", "type": "Center", "arm": 320.0, "conflicts": []},
            "A2": {"deck": "Main", "type": "Center", "arm": 379.0, "conflicts": []},
            "B":  {"deck": "Main", "type": "Center", "arm": 453.0, "conflicts": []},
            "T":  {"deck": "Main", "type": "Center", "arm": 2296.0, "conflicts": []},
        }
        
        for i, z in enumerate(cls.ROW_ZONES):
            arm = cls.CENTROIDS[z]
            cls.MAIN_POSITIONS[f"{z}L"] = {"deck": "Main", "type": "Left",   "arm": arm, "conflicts": [f"{z}C"]}
            cls.MAIN_POSITIONS[f"{z}R"] = {"deck": "Main", "type": "Right",  "arm": arm, "conflicts": [f"{z}C"]}
            
            conflicts = [f"{z}L", f"{z}R"] 
            if i + 1 < len(cls.ROW_ZONES):
                next_z = cls.ROW_ZONES[i+1]
                conflicts.extend([f"{next_z}L", f"{next_z}R", f"{next_z}C"])
            cls.MAIN_POSITIONS[f"{z}C"] = {"deck": "Main", "type": "Center", "arm": arm, "conflicts": conflicts}

        # 2. Filter Disabled Positions
        for pid in list(cls.MAIN_POSITIONS.keys()):
            if pid in cls.DISABLED_POSITIONS:
                del cls.MAIN_POSITIONS[pid]
        
        for pid in list(cls.LOWER_POSITIONS.keys()):
            if pid in cls.DISABLED_POSITIONS:
                del cls.LOWER_POSITIONS[pid]

    @staticmethod
    def get_linear_limit(arm: float) -> float:
        for s, e, l in AircraftMap.LINEAR_LIMITS:
            if s <= arm < e: return l
        return 16.3

AircraftMap.initialize_maps()