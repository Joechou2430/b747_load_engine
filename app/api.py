from typing import List, Dict
from .models import CargoRequest
from .planner.core_engine import CorePlanningEngine

class FlightRepository:
    _flights = {}
    @classmethod
    def get_engine(cls, flight_id, route):
        if flight_id not in cls._flights:
            cls._flights[flight_id] = CorePlanningEngine(route)
        return cls._flights[flight_id]

class SalesIntegrationLayer:
    @staticmethod
    def simulate_loading_needs(cargos: List[CargoRequest]) -> Dict:
        engine = CorePlanningEngine(["DUMMY"])
        return engine.plan_flight(cargos)

    @staticmethod
    def confirm_booking(flight_id: str, route: List[str], cargos: List[CargoRequest]) -> Dict:
        engine = FlightRepository.get_engine(flight_id, route)
        return engine.plan_flight(cargos)