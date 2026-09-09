"""Main fire simulation orchestrator for Track C

Coordinates the complete fire spread simulation:
- Initialization from ignition point(s)
- Environmental data preparation
- Propagation engine execution
- Three-zone geometry extraction
- Risk surface generation
- Exposure calculation
- Result persistence
"""
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import numpy as np
from shapely.geometry import Polygon, MultiPolygon

from modules.geospatial.coordinate_transforms import (
    wgs84_to_metric,
    metric_to_wgs84,
    create_grid_extent,
    DEFAULT_METRIC_CRS
)
from modules.geospatial.terrain_processor import (
    create_flat_dem,
    create_synthetic_dem,
    compute_slope_aspect_vectorized
)
from modules.geospatial.propagation_engine import PropagationEngine
from modules.geospatial.geometry_pipeline import extract_fire_zones, compute_geometry_metrics
from modules.hazards.fire_spread_model import FuelType
from modules.hazards.risk_surface import (
    compute_risk_from_arrival_time,
    serialize_risk_surface,
    risk_statistics
)
from modules.simulation.exposure_calculator import compute_zone_exposure


class FireSimulation:
    """Fire spread simulation orchestrator"""

    def __init__(
        self,
        ignition_lon: float,
        ignition_lat: float,
        ignition_time: datetime,
        simulation_type: str,  # "LIVE" or "SIMULATION"
        incident_id: Optional[str] = None,
        domain_size_m: float = 10000.0,  # 10km x 10km default
        cell_size_m: float = 50.0,  # 50m cells default
        max_time_minutes: float = 180.0,  # 3 hours default
        metric_crs: str = DEFAULT_METRIC_CRS
    ):
        """Initialize fire simulation

        Args:
            ignition_lon: Ignition longitude (WGS84)
            ignition_lat: Ignition latitude (WGS84)
            ignition_time: Ignition timestamp
            simulation_type: "LIVE" (from incident) or "SIMULATION" (manual)
            incident_id: Track B2 incident ID (for LIVE mode)
            domain_size_m: Simulation domain size (square domain)
            cell_size_m: Grid cell size in meters
            max_time_minutes: Maximum simulation time
            metric_crs: Projected CRS for simulation
        """
        self.ignition_lon = ignition_lon
        self.ignition_lat = ignition_lat
        self.ignition_time = ignition_time
        self.simulation_type = simulation_type
        self.incident_id = incident_id
        self.domain_size_m = domain_size_m
        self.cell_size_m = cell_size_m
        self.max_time_minutes = max_time_minutes
        self.metric_crs = metric_crs

        # Grid dimensions
        self.rows = int(domain_size_m / cell_size_m)
        self.cols = int(domain_size_m / cell_size_m)

        # Create grid extent
        self.extent = create_grid_extent(
            center_lon=ignition_lon,
            center_lat=ignition_lat,
            width_m=domain_size_m,
            height_m=domain_size_m,
            metric_crs=metric_crs
        )

        # Convert ignition to grid coordinates
        ignition_x, ignition_y = wgs84_to_metric(ignition_lon, ignition_lat, metric_crs)
        from modules.geospatial.coordinate_transforms import metric_to_grid
        self.ignition_i, self.ignition_j = metric_to_grid(
            ignition_x,
            ignition_y,
            self.extent["origin_x"],
            self.extent["origin_y"],
            cell_size_m
        )

        # Environmental grids (initialized with defaults)
        self.fuel_grid: Optional[np.ndarray] = None
        self.moisture_grid: Optional[np.ndarray] = None
        self.dem: Optional[np.ndarray] = None
        self.slope_grid: Optional[np.ndarray] = None
        self.aspect_grid: Optional[np.ndarray] = None

        # Wind conditions
        self.wind_speed_ms: float = 0.0
        self.wind_from_deg: float = 0.0

        # Results
        self.arrival_time: Optional[np.ndarray] = None
        self.current_geometry: Optional[Polygon | MultiPolygon] = None
        self.warning_geometry: Optional[Polygon | MultiPolygon] = None
        self.projection_geometry: Optional[Polygon | MultiPolygon] = None
        self.risk_surface: Optional[np.ndarray] = None

    def setup_environment(
        self,
        fuel_type: str = "uniform_grass",
        moisture_index: float = 0.3,
        wind_speed_ms: float = 5.0,
        wind_from_deg: float = 270.0,
        dem_type: str = "flat",
        terrain_slope_deg: float = 0.0
    ):
        """Setup environmental data

        Args:
            fuel_type: Fuel configuration ("uniform_grass", "uniform_brush", "mixed")
            moisture_index: Normalized moisture [0, 1]
            wind_speed_ms: Wind speed (m/s)
            wind_from_deg: Wind FROM direction (degrees)
            dem_type: DEM type ("flat", "slope")
            terrain_slope_deg: Terrain slope (degrees, for slope DEM)
        """
        # Create fuel grid
        if fuel_type == "uniform_grass":
            self.fuel_grid = np.full(
                (self.rows, self.cols),
                FuelType.GRASS.value,
                dtype=np.int32
            )
        elif fuel_type == "uniform_brush":
            self.fuel_grid = np.full(
                (self.rows, self.cols),
                FuelType.BRUSH.value,
                dtype=np.int32
            )
        elif fuel_type == "uniform_forest":
            self.fuel_grid = np.full(
                (self.rows, self.cols),
                FuelType.FOREST.value,
                dtype=np.int32
            )
        else:
            # Default to grass
            self.fuel_grid = np.full(
                (self.rows, self.cols),
                FuelType.GRASS.value,
                dtype=np.int32
            )

        # Create moisture grid
        self.moisture_grid = np.full(
            (self.rows, self.cols),
            moisture_index,
            dtype=np.float32
        )

        # Create DEM
        if dem_type == "flat":
            self.dem = create_flat_dem(self.rows, self.cols, elevation_m=100.0)
        elif dem_type == "slope":
            self.dem = create_synthetic_dem(
                self.rows,
                self.cols,
                self.cell_size_m,
                base_elevation_m=100.0,
                slope_deg=terrain_slope_deg,
                slope_direction_deg=45.0  # NE slope
            )
        else:
            self.dem = create_flat_dem(self.rows, self.cols)

        # Compute slope and aspect
        self.slope_grid, self.aspect_grid = compute_slope_aspect_vectorized(
            self.dem,
            self.cell_size_m
        )

        # Set wind conditions
        self.wind_speed_ms = wind_speed_ms
        self.wind_from_deg = wind_from_deg

    def run_propagation(self) -> np.ndarray:
        """Run fire propagation

        Returns:
            Arrival time field
        """
        if self.fuel_grid is None:
            raise ValueError("Environment not setup. Call setup_environment() first.")

        # Create propagation engine
        engine = PropagationEngine(
            fuel_grid=self.fuel_grid,
            moisture_grid=self.moisture_grid,
            slope_grid=self.slope_grid,
            aspect_grid=self.aspect_grid,
            cell_size_m=self.cell_size_m,
            wind_speed_ms=self.wind_speed_ms,
            wind_from_deg=self.wind_from_deg
        )

        # Add ignition point
        engine.add_ignition(self.ignition_i, self.ignition_j, ignition_time=0.0)

        # Run propagation
        self.arrival_time = engine.propagate(max_time_minutes=self.max_time_minutes)

        return self.arrival_time

    def extract_geometries(
        self,
        current_time_minutes: float = 0.0,
        warning_horizon_minutes: float = 30.0,
        projection_horizon_minutes: float = 180.0
    ) -> Tuple[Polygon | MultiPolygon, Polygon | MultiPolygon, Polygon | MultiPolygon]:
        """Extract three-zone fire geometries

        Args:
            current_time_minutes: Current simulation time (minutes from ignition)
            warning_horizon_minutes: Warning zone horizon
            projection_horizon_minutes: Projection zone horizon

        Returns:
            (current_geometry, warning_geometry, projection_geometry)
        """
        if self.arrival_time is None:
            raise ValueError("Propagation not run. Call run_propagation() first.")

        # Extract geometries
        current, warning, projection = extract_fire_zones(
            arrival_time=self.arrival_time,
            current_time=current_time_minutes,
            warning_horizon_minutes=warning_horizon_minutes,
            projection_horizon_minutes=projection_horizon_minutes,
            origin_x=self.extent["origin_x"],
            origin_y=self.extent["origin_y"],
            cell_size_m=self.cell_size_m,
            simplify_tolerance=self.cell_size_m * 0.5  # Simplify to half cell size
        )

        self.current_geometry = current
        self.warning_geometry = warning
        self.projection_geometry = projection

        return current, warning, projection

    def compute_risk(self, current_time_minutes: float = 0.0) -> np.ndarray:
        """Compute risk surface

        Args:
            current_time_minutes: Current simulation time

        Returns:
            Risk surface [0, 1]
        """
        if self.arrival_time is None:
            raise ValueError("Propagation not run. Call run_propagation() first.")

        # Compute risk from arrival time
        self.risk_surface = compute_risk_from_arrival_time(
            arrival_time=self.arrival_time,
            current_time=current_time_minutes,
            max_horizon_minutes=self.max_time_minutes,
            decay_rate=0.02
        )

        return self.risk_surface

    def get_simulation_summary(self) -> Dict:
        """Get simulation summary

        Returns:
            Summary dict
        """
        summary = {
            "ignition": {
                "lon": self.ignition_lon,
                "lat": self.ignition_lat,
                "time": self.ignition_time.isoformat(),
            },
            "domain": {
                "size_m": self.domain_size_m,
                "cell_size_m": self.cell_size_m,
                "rows": self.rows,
                "cols": self.cols,
                "crs": self.metric_crs,
            },
            "environmental": {
                "wind_speed_ms": self.wind_speed_ms,
                "wind_from_deg": self.wind_from_deg,
            },
            "simulation": {
                "type": self.simulation_type,
                "incident_id": self.incident_id,
                "max_time_minutes": self.max_time_minutes,
            },
        }

        if self.current_geometry is not None:
            current_metrics = compute_geometry_metrics(self.current_geometry)
            warning_metrics = compute_geometry_metrics(self.warning_geometry)
            projection_metrics = compute_geometry_metrics(self.projection_geometry)

            summary["geometries"] = {
                "current": current_metrics,
                "warning": warning_metrics,
                "projection": projection_metrics,
            }

        if self.risk_surface is not None:
            risk_stats = risk_statistics(self.risk_surface)
            summary["risk"] = risk_stats

        return summary


def run_fire_simulation(
    ignition_lon: float,
    ignition_lat: float,
    simulation_type: str = "SIMULATION",
    incident_id: Optional[str] = None,
    **kwargs
) -> Dict:
    """Convenience function to run complete fire simulation

    Args:
        ignition_lon: Ignition longitude (WGS84)
        ignition_lat: Ignition latitude (WGS84)
        simulation_type: "LIVE" or "SIMULATION"
        incident_id: Incident ID (for LIVE mode)
        **kwargs: Additional arguments passed to FireSimulation

    Returns:
        Simulation results dict
    """
    # Create simulation
    sim = FireSimulation(
        ignition_lon=ignition_lon,
        ignition_lat=ignition_lat,
        ignition_time=datetime.utcnow(),
        simulation_type=simulation_type,
        incident_id=incident_id,
        **kwargs
    )

    # Setup environment
    sim.setup_environment()

    # Run propagation
    sim.run_propagation()

    # Extract geometries
    sim.extract_geometries()

    # Compute risk
    sim.compute_risk()

    # Get summary
    summary = sim.get_simulation_summary()

    return summary
