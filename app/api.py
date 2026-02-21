from typing import List, Dict, Optional
from .models import CargoRequest
from .planner.core_engine import CorePlanningEngine
from .config import AircraftMap

class FlightRepository:
    """ Simple in-memory storage for flight engines """
    _flights = {}
    
    @classmethod
    def get_engine(cls, flight_id: str, route: List[str]):
        if flight_id not in cls._flights:
            cls._flights[flight_id] = CorePlanningEngine(route)
        return cls._flights[flight_id]

class SalesIntegrationLayer:
    """
    Interface for Sales/RMS systems to interact with the Load Planner.
    """

    @staticmethod
    def simulate_loading_needs(cargos: List[CargoRequest]) -> Dict:
        """
        Stateless simulation for sales inquiries.
        Does not persist data.
        """
        # Create a temporary engine
        engine = CorePlanningEngine(["DUMMY_DEST"])
        return engine.plan_flight(cargos)

    @staticmethod
    def confirm_booking(
        flight_id: str, 
        route: List[str], 
        cargos: List[CargoRequest],
        restrictions: Optional[List[str]] = None
    ) -> Dict:
        """
        Process a booking for a specific flight.
        
        Args:
            flight_id: Unique flight identifier
            route: List of destinations
            cargos: List of cargo requests
            restrictions: List of position IDs that are INOP (e.g. ["42R", "11P"])
        """
        # 1. Get persistent engine instance
        engine = FlightRepository.get_engine(flight_id, route)
        
        # 2. Apply Ad-hoc Restrictions (The Frontend Logic)
        # This allows operators to mark positions as broken on the fly.
        if restrictions:
            print(f"[{flight_id}] Applying ad-hoc restrictions: {restrictions}")
            # Update the global map (Note: In production this should be per-flight instance)
            AircraftMap.DISABLED_POSITIONS.update(restrictions)
            # Re-build the map to remove disabled positions
            AircraftMap.initialize_maps()

        # 3. Run planning logic
        return engine.plan_flight(cargos)