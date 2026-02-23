# app/planner/optimizer.py
from typing import List, Dict, Tuple
from app.models import CargoItem, Position, LoadPlan, DisplacementResult

# --- PHASE 6-B: Revenue Optimization & Displacement Cost Engine ---

class RevenueOptimizer:
    def __init__(self, positions: List[Position], geometry_engine, wb_engine):
        """
        Initialize the optimizer with aircraft positions and constraint engines.
        geometry_engine: Instance of Phase 2 engine (handles overlaps/exclusions).
        wb_engine: Instance of Phase 3 engine (handles Weight & Balance).
        """
        self.positions = {p.name: p for p in positions}
        self.geometry_engine = geometry_engine
        self.wb_engine = wb_engine

    def calculate_displacement(self, cargo: CargoItem, target_pos_name: str, current_load: List[Dict]) -> DisplacementResult:
        """
        Evaluate the displacement cost and profitability of placing a cargo at a specific position.
        """
        if target_pos_name not in self.positions:
            return DisplacementResult(
                cargo_id=cargo.id, target_position=target_pos_name, blocked_positions=[],
                displacement_cost=0.0, net_profit=0.0, is_profitable=False, is_loadable=False,
                rejection_reason="Invalid position"
            )

        target_pos = self.positions[target_pos_name]
        
        # 1. Check basic geometry and structural limits (Phase 2 & 3 integration)
        is_valid, reason = self.geometry_engine.check_fit(cargo, target_pos, current_load)
        if not is_valid:
            return DisplacementResult(
                cargo_id=cargo.id, target_position=target_pos_name, blocked_positions=[],
                displacement_cost=0.0, net_profit=0.0, is_profitable=False, is_loadable=False,
                rejection_reason=f"Geometric/Structural constraint failed: {reason}"
            )

        # 2. Identify blocked positions based on Start/End station overlaps and Lower Deck exclusions
        blocked_positions = self.geometry_engine.get_blocked_positions(cargo, target_pos, self.positions.values())
        
        # 3. Calculate Displacement Cost
        displacement_cost = sum(self.positions[p_name].baseline_value for p_name in blocked_positions)
        
        # 4. Calculate Net Profit
        net_profit = cargo.revenue - displacement_cost
        is_profitable = net_profit > 0

        return DisplacementResult(
            cargo_id=cargo.id,
            target_position=target_pos_name,
            blocked_positions=blocked_positions,
            displacement_cost=displacement_cost,
            net_profit=net_profit,
            is_profitable=is_profitable,
            is_loadable=True
        )

    def optimize_booking_requests(self, pending_cargos: List[CargoItem], current_plan: LoadPlan) -> LoadPlan:
        """
        Greedy optimization for a batch of booking requests to maximize total revenue.
        Sorts cargo by Yield (Revenue / Weight) and attempts to load them.
        """
        # Sort pending cargos by yield (descending)
        # Yield = revenue / weight. If weight is 0, prioritize by revenue.
        sorted_cargos = sorted(
            pending_cargos, 
            key=lambda c: (c.revenue / c.weight) if c.weight > 0 else c.revenue, 
            reverse=True
        )

        optimized_plan = LoadPlan(
            items=current_plan.items.copy(),
            total_weight=current_plan.total_weight,
            total_revenue=current_plan.total_revenue,
            cg_station=current_plan.cg_station,
            mac_percent=current_plan.mac_percent
        )

        current_load_dicts = [{"cargo": item.cargo, "position": item.position_name} for item in optimized_plan.items]
        available_positions = list(self.positions.keys())

        for cargo in sorted_cargos:
            best_result = None
            
            # Evaluate all available positions to find the maximum net profit
            for pos_name in available_positions:
                result = self.calculate_displacement(cargo, pos_name, current_load_dicts)
                
                if result.is_loadable and result.is_profitable:
                    if best_result is None or result.net_profit > best_result.net_profit:
                        best_result = result

            # If a profitable and valid position is found, add to plan
            if best_result:
                optimized_plan.items.append(LoadPlanItem(cargo=cargo, position_name=best_result.target_position))
                optimized_plan.total_weight += cargo.weight
                optimized_plan.total_revenue += cargo.revenue
                
                # Update current load for subsequent iterations
                current_load_dicts.append({"cargo": cargo, "position": best_result.target_position})
                
                # Remove blocked positions from available pool to speed up next iterations
                for blocked in best_result.blocked_positions:
                    if blocked in available_positions:
                        available_positions.remove(blocked)
                        
                # Update W&B (Phase 3 integration)
                optimized_plan.cg_station, optimized_plan.mac_percent = self.wb_engine.calculate_cg(optimized_plan.items, self.positions)

        return optimized_plan