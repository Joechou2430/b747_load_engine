from typing import List, Dict, Tuple
import math
from ..models import CargoRequest, PackedULD, ForcedGroup, PlanningFeedback
from ..config import ULDLibrary, AircraftMap
from ..logic.shoring import ShoringEngine
from ..logic.segregation import SegregationEngine
from ..logic.structural import StructuralEngine
from ..logic.gatekeeper import Gatekeeper
from .math_solver import MathematicalPlanner

class DimensionalPacker:
    """ 3D Geometric packing heuristics """
    @staticmethod
    def calc_max_pieces_per_uld(l: float, w: float, h: float, uld_type: str) -> int:
        spec = ULDLibrary.SPECS.get(uld_type)
        if not spec: return 0
        uld_L = spec['len'] * 2.54 
        uld_W = spec['wid'] * 2.54 
        uld_H = 244.0 if spec['contour'] == 'Q6' else (300.0 if spec['contour'] == 'Q7' else 160.0)
        if uld_type == "M_LOWER": uld_H = 163.0

        if h > uld_H or l > uld_L or w > uld_W: return 0

        base_pcs1 = int(uld_L // l) * int(uld_W // w)
        base_pcs2 = int(uld_L // w) * int(uld_W // l)
        best_base = max(base_pcs1, base_pcs2)
        tiers = int(uld_H // h) if h > 0 else 1
        return best_base * tiers

class CorePlanningEngine:
    def __init__(self, route: List[str]):
        self.route = route
        self.packed_ulds: List[PackedULD] = []
        self.rejected_cargos: List[Dict] = []
        self.action_required: List[PlanningFeedback] = []
        self.math_solver = MathematicalPlanner()

    def _explode_cargos(self, cargos: List[CargoRequest]) -> List[CargoRequest]:
        """ Splits multi-piece cargo requests into individual piece requests """
        exploded = []
        for c in cargos:
            if c.pieces > 1:
                per_piece_wgt = c.weight / c.pieces
                per_piece_vol = c.volume / c.pieces
                for i in range(c.pieces):
                    new_c = CargoRequest(
                        id=f"{c.id}-{i+1}",
                        destination=c.destination,
                        weight=per_piece_wgt,
                        volume=per_piece_vol,
                        pieces=1,
                        dims=c.dims,
                        shc=c.shc,
                        assigned_uld_type=c.assigned_uld_type
                    )
                    exploded.append(new_c)
            else:
                exploded.append(c)
        return exploded

    def plan_flight(self, new_cargos: List[CargoRequest], forced_groups: List[ForcedGroup] = None):
        
        exploded_cargos = self._explode_cargos(new_cargos)
        processed_ids = set()

        # --- PHASE 0: Forced Groups ---
        if forced_groups:
            for group in forced_groups:
                group_cargos = [c for c in exploded_cargos if any(c.id.startswith(gid) for gid in group.cargo_ids)]
                if group_cargos:
                    self._pack_forced_group(group, group_cargos)
                    for c in group_cargos:
                        processed_ids.add(c.id)

        std_cargos = []
        remaining = [c for c in exploded_cargos if c.id not in processed_ids]
        
        # --- PHASE 1: Pre-process ---
        for c in remaining:
            door_check = Gatekeeper.validate_door_entry(c)
            if not door_check["pass"]:
                self.rejected_cargos.append({"id": c.id, "reason": door_check["reason"]})
                continue

            rec = ShoringEngine.recommend_type(c)
            if rec["type"] == "ERROR":
                self.rejected_cargos.append({"id": c.id, "reason": rec["reason"]})
                continue
            
            shore_res = ShoringEngine.calculate_shoring_needs(c, rec["type"], 320)
            if shore_res["needed"]:
                c.weight += shore_res["weight"]
                if c.dims: c.dims[0]['h'] += shore_res["height"]
            
            is_special = (
                c.assigned_uld_type or 
                rec["type"] not in ["M", "M_LOWER", "K"] or 
                c.shc or 
                shore_res["needed"] or
                rec.get("floating", False)
            )
            
            if is_special:
                self._heuristic_pack(c, is_floating=rec.get("floating", False))
                continue

            if c.dims and len(c.dims) > 0:
                self._pack_3d_cargo(c, rec["type"])
            else:
                std_cargos.append(c)

        # --- PHASE 2: Volumetric Top-up ---
        lower_vols = [c for c in std_cargos if 0 < c.max_height <= 163 or c.max_height == 0]
        main_vols = [c for c in std_cargos if c not in lower_vols]
        
        if lower_vols: self._smart_batch_optimize(lower_vols, "M_LOWER")
        if main_vols: self._smart_batch_optimize(main_vols, "M")

        # --- PHASE 3: Allocation ---
        self._allocate_to_aircraft()
        
        return self._generate_report()

    def _pack_forced_group(self, group: ForcedGroup, cargos: List[CargoRequest]):
        target_type = group.target_uld_type
        max_ulds = group.max_uld_count
        spec = ULDLibrary.SPECS.get(target_type)
        if not spec: return

        from ..config import SystemConfig
        eff_vol = spec['max_vol'] * SystemConfig.PACKING_LOSS_FACTOR
        max_net_wgt = spec['max_gross'] - spec['tare']

        group_ulds = [PackedULD(f"FRC-{group.group_id}-{i+1}", target_type, spec['contour'], cargos[0].destination) for i in range(max_ulds)]
        leftovers = []
        sorted_cargos = sorted(cargos, key=lambda x: (x.weight, x.volume), reverse=True)

        for cargo in sorted_cargos:
            placed = False
            for uld in group_ulds:
                if (uld.total_weight + cargo.weight <= max_net_wgt) and (uld.total_volume + cargo.volume <= eff_vol):
                    if all(SegregationEngine.check_mix(uld.shc_codes, s) for s in cargo.shc):
                        uld.items.append(cargo)
                        uld.total_weight += cargo.weight
                        uld.total_volume += cargo.volume
                        uld.shc_codes.update(cargo.shc)
                        placed = True
                        break
            if not placed: leftovers.append(cargo)

        for uld in group_ulds:
            if uld.items:
                uld.status = "CLOSED"; uld.is_pure = True; self.packed_ulds.append(uld)

        if leftovers:
            rem_wgt = sum(c.weight for c in leftovers)
            msg = f"Group {group.group_id} overflow: {len(leftovers)} pcs ({rem_wgt:.1f}kg)."
            self.action_required.append(PlanningFeedback(group.group_id, msg, leftovers))

    def _pack_3d_cargo(self, cargo: CargoRequest, suggested_type: str):
        dim = cargo.dims[0]
        l, w, h = dim['l'], dim['w'], dim['h']
        pcs_left = cargo.pieces
        
        max_pcs_per_uld = DimensionalPacker.calc_max_pieces_per_uld(l, w, h, suggested_type)
        if max_pcs_per_uld <= 0:
            self.rejected_cargos.append({"id": cargo.id, "reason": f"Dims cannot fit {suggested_type}"})
            return

        spec = ULDLibrary.SPECS[suggested_type]
        per_pc_weight = cargo.weight / cargo.pieces
        per_pc_vol = cargo.volume / cargo.pieces

        while pcs_left > 0:
            max_by_weight = int((spec['max_gross'] - spec['tare']) // per_pc_weight)
            if max_by_weight <= 0:
                self.rejected_cargos.append({"id": f"{cargo.id}-rem", "reason": "Single piece too heavy"})
                break

            pcs_this_uld = min(pcs_left, max_pcs_per_uld, max_by_weight)
            
            new_uld = PackedULD(f"3D-{len(self.packed_ulds)+1:03d}", suggested_type, spec['contour'], cargo.destination)
            chunk_cargo = CargoRequest(f"{cargo.id} ({pcs_this_uld}p)", cargo.destination, per_pc_weight * pcs_this_uld, per_pc_vol * pcs_this_uld, pcs_this_uld, cargo.dims, cargo.shc)
            
            new_uld.items.append(chunk_cargo)
            new_uld.total_weight += chunk_cargo.weight
            new_uld.total_volume += chunk_cargo.volume
            new_uld.shc_codes.update(chunk_cargo.shc)
            
            if new_uld.total_weight + spec['tare'] >= spec['max_gross'] * 0.95: new_uld.status = "CLOSED"
            else: new_uld.status = "OPEN"
                
            self.packed_ulds.append(new_uld)
            pcs_left -= pcs_this_uld

    def _smart_batch_optimize(self, cargos: List[CargoRequest], target_uld_type: str):
        groups = {}
        exploded = []
        for c in cargos:
            if c.pieces > 1:
                w_pc = c.weight / c.pieces; v_pc = c.volume / c.pieces
                for i in range(c.pieces): exploded.append(CargoRequest(f"{c.id}-{i+1}", c.destination, w_pc, v_pc, 1, [], c.shc))
            else: exploded.append(c)
                
        for c in exploded:
            if c.destination not in groups: groups[c.destination] = []
            groups[c.destination].append(c)
            
        spec = ULDLibrary.SPECS[target_uld_type]
        from ..config import SystemConfig
        max_effective_vol = spec['max_vol'] * SystemConfig.PACKING_LOSS_FACTOR
        max_net_weight = spec['max_gross'] - spec['tare']

        for dest, items in groups.items():
            remaining_items = []
            for item in items:
                packed = False
                for uld in self.packed_ulds:
                    if uld.status == "OPEN" and uld.destination == dest and uld.uld_type == target_uld_type:
                        if not all(SegregationEngine.check_mix(uld.shc_codes, s) for s in item.shc): continue
                        if (uld.total_weight + item.weight <= max_net_weight) and (uld.total_volume + item.volume <= max_effective_vol):
                            uld.items.append(item); uld.total_weight += item.weight; uld.total_volume += item.volume; uld.shc_codes.update(item.shc); packed = True; break
                if not packed: remaining_items.append(item)
            
            if remaining_items:
                res = self.math_solver.optimize(remaining_items, target_uld_type)
                for u in res: u.id = f"OPT-{len(self.packed_ulds)+1:03d}"; self.packed_ulds.append(u)

    def _heuristic_pack(self, cargo: CargoRequest, is_floating: bool = False):
        rec = ShoringEngine.recommend_type(cargo)
        target_type = cargo.assigned_uld_type or rec["type"]
        
        if not is_floating:
            for uld in self.packed_ulds:
                if uld.uld_type == target_type and uld.status == "OPEN" and uld.destination == cargo.destination:
                     if not all(SegregationEngine.check_mix(uld.shc_codes, s) for s in cargo.shc): continue
                     spec = ULDLibrary.SPECS[target_type]
                     if uld.gross_weight + cargo.weight <= spec['max_gross']:
                         uld.items.append(cargo); uld.total_weight += cargo.weight; uld.total_volume += cargo.volume; uld.shc_codes.update(cargo.shc); return
        
        new_id = f"FLT-{len(self.packed_ulds)+1:03d}" if is_floating else f"SPL-{len(self.packed_ulds)+1:03d}"
        new_uld = PackedULD(id=new_id, uld_type=target_type, contour=ULDLibrary.SPECS[target_type]['contour'], destination=cargo.destination)
        if is_floating: new_uld.status = "CLOSED"; new_uld.shoring_note = "FLOATING LOAD"
        new_uld.items.append(cargo); new_uld.total_weight += cargo.weight; new_uld.total_volume += cargo.volume; new_uld.shc_codes.update(cargo.shc); self.packed_ulds.append(new_uld)

    def _allocate_to_aircraft(self):
        occupied = set()
        ulds = sorted(self.packed_ulds, key=lambda x: (x.uld_type not in ["G", "R"], x.uld_type not in ["M_LOWER", "A_LOWER"], x.uld_type != "K"))
        for uld in ulds:
            if uld.assigned_position: continue
            candidates = []
            if uld.uld_type in ["G", "R"]: candidates = [(k,v) for k,v in AircraftMap.MAIN_POSITIONS.items() if v['type'] == 'Center']
            elif uld.uld_type in ["M", "A"]: candidates = [(k,v) for k,v in AircraftMap.MAIN_POSITIONS.items() if v['type'] in ['Left', 'Right']]
            elif uld.uld_type in ["M_LOWER", "A_LOWER"]: candidates = [(k,v) for k,v in AircraftMap.LOWER_POSITIONS.items() if v['type'] == 'Center']
            elif uld.uld_type == "K": candidates = [(k,v) for k,v in AircraftMap.LOWER_POSITIONS.items() if v['type'] in ['Left', 'Right']]
            
            candidates.sort(key=lambda x: x[1]['arm'])
            assigned = False
            for pid, info in candidates:
                if pid in occupied: continue
                conflict = False
                for c in info.get("conflicts", []):
                    if c in occupied: conflict = True; break
                if conflict: continue
                for occ_pid in occupied:
                    occ_info = AircraftMap.MAIN_POSITIONS.get(occ_pid) or AircraftMap.LOWER_POSITIONS.get(occ_pid)
                    if occ_info and pid in occ_info.get("conflicts", []): conflict = True; break
                if conflict: continue
                if not StructuralEngine.check_linear_load(uld, info['arm'])[0]: continue
                uld.assigned_position = pid; uld.assigned_arm = info['arm']; occupied.add(pid); assigned = True; break
            if not assigned: uld.assigned_position = "UNASSIGNED"

    def _generate_report(self):
        zone_warnings = StructuralEngine.check_zone_limits(self.packed_ulds)
        vis_data = []
        for u in self.packed_ulds:
            if u.assigned_position != "UNASSIGNED":
                cargo_details = []
                for item in u.items:
                    shc_str = f" [{','.join(item.shc)}]" if item.shc else ""
                    cargo_details.append(f"{item.id} ({item.weight:.0f}kg, {item.destination}{shc_str})")
                vis_data.append({"pos": u.assigned_position, "uld": u.id, "type": u.uld_type, "weight": f"{u.gross_weight:.0f}", "arm": u.assigned_arm, "dest": u.destination, "contents": cargo_details})
        
        action_req_json = []
        for req in self.action_required:
            action_req_json.append({"group_id": req.group_id, "message": req.message, "leftover_count": len(req.remaining_cargos)})

        return {"summary": {"total_ulds": len(self.packed_ulds), "total_weight": sum(u.gross_weight for u in self.packed_ulds), "warnings": zone_warnings}, "rejected": self.rejected_cargos, "action_required": action_req_json, "visualization": vis_data}