from typing import List
from ortools.linear_solver import pywraplp
from ..models import CargoRequest, PackedULD
from ..config import ULDLibrary, SystemConfig

class MathematicalPlanner:
    def __init__(self):
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
    def optimize(self, cargos: List[CargoRequest], uld_type: str) -> List[PackedULD]:
        if not cargos or not self.solver: return []
        
        spec = ULDLibrary.SPECS[uld_type]
        cap_w = spec['max_gross'] - spec['tare']
        cap_v = spec['max_vol'] * SystemConfig.PACKING_LOSS_FACTOR
        
        max_bins = int((sum(c.volume for c in cargos)/cap_v)*1.2) + 2
        x, y = {}, {}
        
        for j in range(max_bins):
            y[j] = self.solver.IntVar(0, 1, f'bin_{j}')
            for i in range(len(cargos)):
                x[i,j] = self.solver.IntVar(0, 1, f'x_{i}_{j}')

        for i in range(len(cargos)):
            self.solver.Add(self.solver.Sum([x[i,j] for j in range(max_bins)]) == 1)

        for j in range(max_bins):
            self.solver.Add(self.solver.Sum([cargos[i].weight * x[i,j] for i in range(len(cargos))]) <= cap_w * y[j])
            self.solver.Add(self.solver.Sum([cargos[i].volume * x[i,j] for i in range(len(cargos))]) <= cap_v * y[j])

        self.solver.Minimize(self.solver.Sum([y[j] for j in range(max_bins)]))
        status = self.solver.Solve()
        
        results = []
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            for j in range(max_bins):
                if y[j].solution_value() > 0.5:
                    items = [cargos[i] for i in range(len(cargos)) if x[i,j].solution_value() > 0.5]
                    if items:
                        new_uld = PackedULD("TEMP", uld_type, spec['contour'], items[0].destination)
                        for it in items:
                            new_uld.items.append(it)
                            new_uld.total_weight += it.weight
                            new_uld.total_volume += it.volume
                            new_uld.shc_codes.update(it.shc)
                        results.append(new_uld)
        return results