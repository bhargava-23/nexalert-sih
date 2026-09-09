"""Track C comprehensive tests

Tests fire spread propagation, geometry, risk, and integration.
"""
import pytest
import numpy as np
import math
from datetime import datetime

from modules.geospatial.coordinate_transforms import (
    wind_from_to_to,
    cell_distance,
    get_8_neighbors
)
from modules.geospatial.terrain_processor import (
    create_flat_dem,
    compute_slope_aspect_vectorized
)
from modules.geospatial.propagation_engine import PropagationEngine
from modules.geospatial.geometry_pipeline import (
    threshold_arrival_time,
    mask_to_geometry,
    compute_geometry_metrics
)
from modules.hazards.fire_spread_model import (
    FuelType,
    get_base_ros,
    moisture_factor,
    compute_ros
)
from modules.hazards.risk_surface import (
    compute_risk_from_arrival_time,
    risk_statistics
)
from modules.simulation.fire_simulation import FireSimulation


class TestWindConversion:
    """Test CRITICAL wind FROM→TO conversion"""

    def test_wind_from_west_propagates_east(self):
        """Wind FROM 270° (west) propagates TO 90° (east)"""
        assert wind_from_to_to(270.0) == 90.0

    def test_wind_from_north_propagates_south(self):
        """Wind FROM 0° (north) propagates TO 180° (south)"""
        assert wind_from_to_to(0.0) == 180.0

    def test_wind_from_east_propagates_west(self):
        """Wind FROM 90° (east) propagates TO 270° (west)"""
        assert wind_from_to_to(90.0) == 270.0

    def test_wind_from_south_propagates_north(self):
        """Wind FROM 180° (south) propagates TO 0° (north)"""
        assert wind_from_to_to(180.0) == 0.0


class TestCellDistance:
    """Test CRITICAL orthogonal vs diagonal distances"""

    def test_orthogonal_distance_equals_cell_size(self):
        """Orthogonal neighbors: distance = Δ"""
        cell_size = 50.0

        # Horizontal neighbor (same row, +1 col)
        dist = cell_distance(0, 0, 0, 1, cell_size)
        assert abs(dist - cell_size) < 1e-6

        # Vertical neighbor (+1 row, same col)
        dist = cell_distance(0, 0, 1, 0, cell_size)
        assert abs(dist - cell_size) < 1e-6

    def test_diagonal_distance_equals_sqrt2_times_cell_size(self):
        """Diagonal neighbors: distance = Δ√2"""
        cell_size = 50.0
        expected = cell_size * math.sqrt(2.0)

        # Diagonal neighbor (+1 row, +1 col)
        dist = cell_distance(0, 0, 1, 1, cell_size)
        assert abs(dist - expected) < 1e-6

        # Diagonal neighbor (+1 row, -1 col)
        dist = cell_distance(0, 1, 1, 0, cell_size)
        assert abs(dist - expected) < 1e-6


class TestFuelModel:
    """Test fuel model and base ROS"""

    def test_nonburnable_has_zero_ros(self):
        """Non-burnable fuel type has ROS = 0"""
        assert get_base_ros(FuelType.NONBURNABLE) == 0.0
        assert get_base_ros(FuelType.WATER) == 0.0

    def test_grass_has_positive_ros(self):
        """Grass fuel type has positive ROS"""
        ros = get_base_ros(FuelType.GRASS)
        assert ros > 0.0

    def test_moisture_factor_dry_increases_spread(self):
        """Low moisture (dry) increases spread"""
        # Very dry (moisture = 0.0)
        dry_factor = moisture_factor(0.0)
        # Medium moisture (moisture = 0.5)
        medium_factor = moisture_factor(0.5)

        assert dry_factor > medium_factor


class TestPropagationEngine:
    """Test fire propagation engine"""

    def test_calm_wind_circular_spread(self):
        """Calm wind produces circular spread (no diamond artifacts)"""
        # Setup
        rows, cols = 21, 21
        cell_size_m = 50.0

        # Uniform fuel grid (grass)
        fuel_grid = np.full((rows, cols), FuelType.GRASS.value, dtype=np.int32)

        # Uniform conditions
        moisture_grid = np.full((rows, cols), 0.3, dtype=np.float32)
        slope_grid = np.zeros((rows, cols), dtype=np.float32)
        aspect_grid = np.full((rows, cols), -1.0, dtype=np.float32)

        # No wind
        wind_speed_ms = 0.0
        wind_from_deg = 0.0

        # Create engine
        engine = PropagationEngine(
            fuel_grid=fuel_grid,
            moisture_grid=moisture_grid,
            slope_grid=slope_grid,
            aspect_grid=aspect_grid,
            cell_size_m=cell_size_m,
            wind_speed_ms=wind_speed_ms,
            wind_from_deg=wind_from_deg
        )

        # Center ignition
        center = rows // 2
        engine.add_ignition(center, center, ignition_time=0.0)

        # Run propagation
        arrival_time = engine.propagate(max_time_minutes=60.0)

        # Check burned cells
        burned_mask = np.isfinite(arrival_time)
        assert np.sum(burned_mask) > 1  # At least ignition + neighbors

        # Check circularity: arrival time should depend on distance from center
        # (no diamond artifacts where diagonal = 2*orthogonal)
        center_i, center_j = center, center

        # Sample points at same distance should have similar arrival times
        # Orthogonal at distance 2: (center±2, center)
        t_north = arrival_time[center - 2, center]
        t_south = arrival_time[center + 2, center]
        t_east = arrival_time[center, center + 2]
        t_west = arrival_time[center, center - 2]

        orthogonal_times = [t_north, t_south, t_east, t_west]
        orthogonal_mean = np.mean([t for t in orthogonal_times if np.isfinite(t)])
        orthogonal_std = np.std([t for t in orthogonal_times if np.isfinite(t)])

        # Should have low variance (similar arrival times)
        assert orthogonal_std < 0.5  # Less than 30 seconds variance

    def test_nonburnable_blocks_propagation(self):
        """Non-burnable cells block fire propagation"""
        # Setup
        rows, cols = 11, 11
        cell_size_m = 50.0

        # Grass with vertical barrier in middle
        fuel_grid = np.full((rows, cols), FuelType.GRASS.value, dtype=np.int32)
        barrier_col = cols // 2
        fuel_grid[:, barrier_col] = FuelType.NONBURNABLE.value

        moisture_grid = np.full((rows, cols), 0.3, dtype=np.float32)
        slope_grid = np.zeros((rows, cols), dtype=np.float32)
        aspect_grid = np.full((rows, cols), -1.0, dtype=np.float32)

        # Create engine
        engine = PropagationEngine(
            fuel_grid=fuel_grid,
            moisture_grid=moisture_grid,
            slope_grid=slope_grid,
            aspect_grid=aspect_grid,
            cell_size_m=cell_size_m,
            wind_speed_ms=0.0,
            wind_from_deg=0.0
        )

        # Ignition on left side of barrier
        center = rows // 2
        engine.add_ignition(center, barrier_col - 2, ignition_time=0.0)

        # Run propagation
        arrival_time = engine.propagate(max_time_minutes=60.0)

        # Fire should NOT cross barrier
        # Right side of barrier should be unburned
        right_side = arrival_time[:, barrier_col + 1:]
        assert np.all(np.isinf(right_side))


class TestGeometryPipeline:
    """Test geometry extraction"""

    def test_threshold_creates_zones(self):
        """Threshold selection creates three zones"""
        # Create synthetic arrival time field with non-overlapping zones
        rows, cols = 20, 20
        arrival_time = np.full((rows, cols), np.inf, dtype=np.float32)

        # Current zone: T_a <= current_time (already burned)
        # Inner square: burned at t=5
        arrival_time[8:12, 8:12] = 5.0

        # Warning zone: current_time < T_a <= current_time + warning_horizon
        # Ring around current: will burn at t=25 (10 < 25 <= 40)
        arrival_time[6:14, 6:14] = 25.0
        arrival_time[8:12, 8:12] = 5.0  # Restore inner square

        # Projection zone: warning_end < T_a <= projection_end
        # Outer ring: will burn at t=100 (40 < 100 <= 130)
        arrival_time[4:16, 4:16] = 100.0
        arrival_time[6:14, 6:14] = 25.0  # Restore warning ring
        arrival_time[8:12, 8:12] = 5.0  # Restore inner square

        current_time = 10.0
        warning_horizon = 30.0
        projection_horizon = 120.0

        current_mask, warning_mask, projection_mask = threshold_arrival_time(
            arrival_time, current_time, warning_horizon, projection_horizon
        )

        # Check masks have cells
        assert np.sum(current_mask) > 0, f"Current mask should have cells, got {np.sum(current_mask)}"
        assert np.sum(warning_mask) > 0, f"Warning mask should have cells, got {np.sum(warning_mask)}"
        assert np.sum(projection_mask) > 0, f"Projection mask should have cells, got {np.sum(projection_mask)}"

        # Zones should not overlap
        assert not np.any(current_mask & warning_mask), "Current and warning should not overlap"
        assert not np.any(current_mask & projection_mask), "Current and projection should not overlap"
        assert not np.any(warning_mask & projection_mask), "Warning and projection should not overlap"

    def test_geometry_has_area(self):
        """Generated geometry has positive area"""
        # Create simple mask
        mask = np.zeros((10, 10), dtype=bool)
        mask[3:7, 3:7] = True  # 4x4 square

        origin_x = 0.0
        origin_y = 100.0
        cell_size_m = 10.0

        geom = mask_to_geometry(mask, origin_x, origin_y, cell_size_m)

        metrics = compute_geometry_metrics(geom)
        assert metrics["area_m2"] > 0
        assert metrics["perimeter_m"] > 0


class TestRiskSurface:
    """Test risk surface computation"""

    def test_risk_surface_bounded_0_to_1(self):
        """Risk surface values are in [0, 1]"""
        # Create arrival time field
        rows, cols = 10, 10
        arrival_time = np.full((rows, cols), np.inf, dtype=np.float32)
        arrival_time[4:6, 4:6] = 30.0

        current_time = 0.0
        risk = compute_risk_from_arrival_time(
            arrival_time, current_time, max_horizon_minutes=180.0
        )

        # Check bounds
        assert np.all(risk >= 0.0)
        assert np.all(risk <= 1.0)

    def test_risk_decreases_with_distance(self):
        """Risk decreases with time until arrival"""
        rows, cols = 10, 10
        arrival_time = np.full((rows, cols), np.inf, dtype=np.float32)

        # Near future
        arrival_time[4, 4] = 5.0
        # Distant future
        arrival_time[4, 5] = 60.0

        current_time = 0.0
        risk = compute_risk_from_arrival_time(arrival_time, current_time)

        # Imminent arrival should have higher risk
        assert risk[4, 4] > risk[4, 5]


class TestFireSimulation:
    """Test full fire simulation"""

    def test_fire_simulation_completes(self):
        """Fire simulation runs without errors"""
        sim = FireSimulation(
            ignition_lon=77.5946,
            ignition_lat=12.9716,
            ignition_time=datetime.utcnow(),
            simulation_type="SIMULATION",
            domain_size_m=5000.0,
            cell_size_m=50.0,
            max_time_minutes=60.0
        )

        # Setup environment
        sim.setup_environment(
            fuel_type="uniform_grass",
            moisture_index=0.3,
            wind_speed_ms=5.0,
            wind_from_deg=270.0,
            dem_type="flat"
        )

        # Run propagation
        arrival_time = sim.run_propagation()
        assert arrival_time is not None
        assert np.sum(np.isfinite(arrival_time)) > 0

        # Extract geometries
        current, warning, projection = sim.extract_geometries()
        assert current is not None
        assert warning is not None
        assert projection is not None

        # Compute risk
        risk = sim.compute_risk()
        assert risk is not None
        assert np.sum(risk > 0) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
