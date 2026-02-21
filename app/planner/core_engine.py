from typing import List, Dict
from ..models import CargoRequest, PackedULD
from ..config import ULDLibrary, AircraftMap
from ..logic.shoring import ShoringEngine
from ..logic.segregation import SegregationEngine
from ..logic.structural import StructuralEngine
from ..logic.gatekeeper import Gatekeeper
from .math_solver import MathematicalPlanner

class CorePlanningEngine:
    def __init__(self, route: List[str]):
        self.route = route
        self.packed_ulds: List[PackedULD] = []
        self.rejected_cargos: List[Dict] = []
        self.math_solver = MathematicalPlanner()

    def plan_flight(self, new_cargos: List[CargoRequest]):
        std_cargos = []
        
        for c in new_cargos:
            # 1. Door Validation
            door_check = Gatekeeper.validate_door_entry(c)
            if not door_check["pass"]:
                self.rejected_cargos.append({"id": c.id, "reason": door_check["reason"]})
                continue

            # 2. Shoring Calculation
            rec = ShoringEngine.recommend_type(c)
            shore_res = ShoringEngine.calculate_shoring_needs(c, rec["type"], 320)
            
            if shore_res["needed"]:
                c.weight += shore_res["weight"]
                c.dims[0]['h'] += shore_res["height"]
            
            # 3. Identify Special Cargo
            is_special = (
                c.assigned_uld_type or 
                rec["type"] not in ["M", "M_LOWER", "K"] or 
                c.shc or 
                shore_res["needed"]
            )
            
            if is_special:
                self._heuristic_pack(c)
            else:
                std_cargos.append(c)
        
        # 4. Batch Optimization
        lower_cargos = [c for c in std_cargos if 0 < c.max_height <= 163]
        main_cargos = [c for c in std_cargos if c not in lower_cargos]
        
        if lower_cargos: self._batch_optimize(lower_cargos, "M_LOWER")
        if main_cargos: self._batch_optimize(main_cargos, "M")

        # 5. Aircraft Allocation
        self._allocate_to_aircraft()
        
        return self._generate_report()

    def _batch_optimize(self, cargos: List[CargoRequest], uld_type: str):
        groups = {}
        for c in cargos:
            if c.destination not in groups: groups[c.destination] = []
            groups[c.destination].append(c)
            
        for dest, items in groups.items():
            res = self.math_solver.optimize(items, uld_type)
            for u in res:
                u.id = f"OPT-{len(self.packed_ulds)+1:03d}"
                self.packed_ulds.append(u)

    def _heuristic_pack(self, cargo: CargoRequest):
        rec = ShoringEngine.recommend_type(cargo)
        target_type = cargo.assigned_uld_type or rec["type"]
        
        for uld in self.packed_ulds:
            if uld.uld_type == target_type and uld.status == "OPEN" and uld.destination == cargo.destination:
                 if not all(SegregationEngine.check_mix(uld.shc_codes, s) for s in cargo.shc): continue
                 
                 spec = ULDLibrary.SPECS[target_type]
                 if uld.gross_weight + cargo.weight <= spec['max_gross']:
                     uld.items.append(cargo)
                     uld.total_weight += cargo.weight
                     uld.total_volume += cargo.volume
                     uld.shc_codes.update(cargo.shc)
                     return
        
        new_uld = PackedULD(f"SPL-{len(self.packed_ulds)+1:03d}", target_type, ULDLibrary.SPECS[target_type]['contour'], cargo.destination)
        new_uld.items.append(cargo)
        new_uld.total_weight += cargo.weight
        new_uld.total_volume += cargo.volume
        new_uld.shc_codes.update(cargo.shc)
        self.packed_ulds.append(new_uld)

    def _allocate_to_aircraft(self):
        occupied = set()
        ulds = sorted(self.packed_ulds, key=lambda x: (
            x.uld_type not in ["G", "R"], 
            x.uld_type not in ["M_LOWER", "A_LOWER"], 
            x.uld_type != "K"
        ))
        
        for uld in ulds:
            if uld.assigned_position: continue
            
            candidates = []
            if uld.uld_type in ["G", "R"]:
                candidates = [(k,v) for k,v in AircraftMap.MAIN_POSITIONS.items() if v['type'] == 'Center']
            elif uld.uld_type in ["M", "A"]:
                candidates = [(k,v) for k,v in AircraftMap.MAIN_POSITIONS.items() if v['type'] in ['Left', 'Right']]
            elif uld.uld_type in ["M_LOWER", "A_LOWER"]:
                candidates = [(k,v) for k,v in AircraftMap.LOWER_POSITIONS.items() if v['type'] == 'Center']
            elif uld.uld_type == "K":
                candidates = [(k,v) for k,v in AircraftMap.LOWER_POSITIONS.items() if v['type'] in ['Left', 'Right']]
            
            candidates.sort(key=lambda x: x[1]['arm'])
            
            assigned = False
            for pid, info in candidates:
                if pid in occupied: continue
                
                # Check My Conflicts
                conflict = False
                for c in info.get("conflicts", []):
                    if c in occupied: conflict = True; break
                if conflict: continue
                
                # Reverse Check
                for occ_pid in occupied:
                    occ_info = AircraftMap.MAIN_POSITIONS.get(occ_pid) or AircraftMap.LOWER_POSITIONS.get(occ_pid)
                    if occ_info and pid in occ_info.get("conflicts", []):
                        conflict = True; break
                if conflict: continue

                if not StructuralEngine.check_placement(uld, info['arm']): continue
                
                uld.assigned_position = pid
                uld.assigned_arm = info['arm']
                occupied.add(pid)
                assigned = True
                break
            
            if not assigned: uld.assigned_position = "UNASSIGNED"

    def _generate_report(self):
        # Perform Final Structural Checks
        zone_warnings = StructuralEngine.check_zone_limits(self.packed_ulds)
        
        return {
            "summary": {
                "total_ulds": len(self.packed_ulds), 
                "total_weight": sum(u.gross_weight for u in self.packed_ulds),
                "warnings": zone_warnings
            },
            "rejected": self.rejected_cargos,
            "visualization": [
                {"pos": u.assigned_position, "uld": u.id, "type": u.uld_type, "weight": f"{u.gross_weight:.0f}", "arm": u.assigned_arm} 
                for u in self.packed_ulds if u.assigned_position != "UNASSIGNED"
            ]
        }