"""Priority-queue fire propagation engine for Track C

Implements arrival-time propagation using min-heap priority queue:
- 8-neighbor connectivity
- Orthogonal distance = Δ, diagonal distance = Δ√2
- Directional ROS from fire_spread_model
- Non-burnable cells block propagation
- Multiple ignition points supported
"""
import heapq
import math
from typing import List, Tuple, Optional, Set
import numpy as np

from modules.geospatial.coordinate_transforms import get_8_neighbors, cell_distance
from modules.hazards.fire_spread_model import ros_to_neighbor, FuelType


class PropagationEngine:
    """Priority-queue arrival-time propagation engine"""

    def __init__(
        self,
        fuel_grid: np.ndarray,
        moisture_grid: np.ndarray,
        slope_grid: np.ndarray,
        aspect_grid: np.ndarray,
        cell_size_m: float,
        wind_speed_ms: float,
        wind_from_deg: float
    ):
        """Initialize propagation engine

        Args:
            fuel_grid: Fuel type grid (int, FuelType enum values)
            moisture_grid: Moisture index grid [0, 1]
            slope_grid: Slope grid (radians)
            aspect_grid: Aspect grid (radians, -1 = flat)
            cell_size_m: Grid cell size in meters
            wind_speed_ms: Wind speed (m/s)
            wind_from_deg: Wind FROM direction (degrees)
        """
        self.fuel_grid = fuel_grid
        self.moisture_grid = moisture_grid
        self.slope_grid = slope_grid
        self.aspect_grid = aspect_grid
        self.cell_size_m = cell_size_m
        self.wind_speed_ms = wind_speed_ms
        self.wind_from_deg = wind_from_deg

        self.rows, self.cols = fuel_grid.shape

        # Arrival time field (infinite = not reached)
        self.arrival_time = np.full((self.rows, self.cols), np.inf, dtype=np.float32)

        # Priority queue: (arrival_time, i, j)
        self.queue: List[Tuple[float, int, int]] = []

        # Visited cells (to avoid re-processing)
        self.visited: Set[Tuple[int, int]] = set()

    def add_ignition(self, i: int, j: int, ignition_time: float = 0.0):
        """Add ignition point

        Args:
            i: Row index
            j: Column index
            ignition_time: Ignition time (default 0.0)
        """
        if not (0 <= i < self.rows and 0 <= j < self.cols):
            raise ValueError(f"Ignition point ({i}, {j}) out of bounds")

        # Check if burnable
        fuel_value = int(self.fuel_grid[i, j])
        fuel_type = FuelType(fuel_value)

        if fuel_type == FuelType.NONBURNABLE or fuel_type == FuelType.WATER:
            raise ValueError(f"Cannot ignite non-burnable cell at ({i}, {j})")

        # Set arrival time
        self.arrival_time[i, j] = ignition_time

        # Add to priority queue
        heapq.heappush(self.queue, (ignition_time, i, j))

    def propagate(self, max_time_minutes: float = 120.0) -> np.ndarray:
        """Run propagation until queue empty or max time reached

        CRITICAL: Uses priority queue (min-heap) for arrival-time propagation.
        Each cell processes exactly once (earliest arrival wins).

        Algorithm:
        1. Pop cell with earliest arrival time
        2. For each 8-neighbor:
           - Calculate distance (orthogonal Δ, diagonal Δ√2)
           - Calculate ROS from current cell to neighbor
           - Calculate travel time = distance / ROS
           - Update neighbor arrival time if earlier
           - Push neighbor to queue

        Args:
            max_time_minutes: Maximum simulation time (minutes)

        Returns:
            Arrival time field (minutes, np.inf = not reached)
        """
        while self.queue:
            # Pop cell with earliest arrival time
            current_time, i, j = heapq.heappop(self.queue)

            # Skip if already visited (earlier arrival already processed)
            if (i, j) in self.visited:
                continue

            # Mark as visited
            self.visited.add((i, j))

            # Stop if max time exceeded
            if current_time > max_time_minutes:
                break

            # Process 8 neighbors
            for ni, nj in get_8_neighbors(i, j, self.rows, self.cols):
                # Skip if already visited
                if (ni, nj) in self.visited:
                    continue

                # Check if neighbor is burnable
                fuel_value = int(self.fuel_grid[ni, nj])
                fuel_type = FuelType(fuel_value)

                if fuel_type == FuelType.NONBURNABLE or fuel_type == FuelType.WATER:
                    # Non-burnable: skip (fire cannot cross)
                    continue

                # Calculate distance (CRITICAL: orthogonal vs diagonal)
                distance_m = cell_distance(i, j, ni, nj, self.cell_size_m)

                # Calculate ROS from current cell to neighbor
                ros_m_per_min = ros_to_neighbor(
                    from_i=i,
                    from_j=j,
                    to_i=ni,
                    to_j=nj,
                    fuel_grid=self.fuel_grid,
                    moisture_grid=self.moisture_grid,
                    slope_grid=self.slope_grid,
                    aspect_grid=self.aspect_grid,
                    wind_speed_ms=self.wind_speed_ms,
                    wind_from_deg=self.wind_from_deg
                )

                if ros_m_per_min <= 0.0:
                    # Zero ROS: cannot propagate
                    continue

                # Calculate travel time
                travel_time_min = distance_m / ros_m_per_min

                # Candidate arrival time
                candidate_arrival = current_time + travel_time_min

                # Update if earlier than current arrival time
                if candidate_arrival < self.arrival_time[ni, nj]:
                    self.arrival_time[ni, nj] = candidate_arrival

                    # Push to priority queue
                    heapq.heappush(self.queue, (candidate_arrival, ni, nj))

        return self.arrival_time

    def get_statistics(self) -> dict:
        """Get propagation statistics

        Returns:
            Statistics dict
        """
        burned_mask = np.isfinite(self.arrival_time)
        burned_count = np.sum(burned_mask)
        total_count = self.rows * self.cols

        if burned_count > 0:
            min_time = float(np.min(self.arrival_time[burned_mask]))
            max_time = float(np.max(self.arrival_time[burned_mask]))
            mean_time = float(np.mean(self.arrival_time[burned_mask]))
        else:
            min_time = max_time = mean_time = 0.0

        return {
            "cells_burned": int(burned_count),
            "cells_total": int(total_count),
            "fraction_burned": float(burned_count) / total_count if total_count > 0 else 0.0,
            "min_arrival_time": min_time,
            "max_arrival_time": max_time,
            "mean_arrival_time": mean_time,
            "cells_visited": len(self.visited),
        }


def propagate_fire(
    fuel_grid: np.ndarray,
    moisture_grid: np.ndarray,
    slope_grid: np.ndarray,
    aspect_grid: np.ndarray,
    ignition_points: List[Tuple[int, int]],
    cell_size_m: float,
    wind_speed_ms: float,
    wind_from_deg: float,
    max_time_minutes: float = 120.0
) -> np.ndarray:
    """Convenience function for fire propagation

    Args:
        fuel_grid: Fuel type grid (int, FuelType enum values)
        moisture_grid: Moisture index grid [0, 1]
        slope_grid: Slope grid (radians)
        aspect_grid: Aspect grid (radians, -1 = flat)
        ignition_points: List of (i, j) ignition cell indices
        cell_size_m: Grid cell size in meters
        wind_speed_ms: Wind speed (m/s)
        wind_from_deg: Wind FROM direction (degrees)
        max_time_minutes: Maximum simulation time (minutes)

    Returns:
        Arrival time field (minutes, np.inf = not reached)
    """
    engine = PropagationEngine(
        fuel_grid=fuel_grid,
        moisture_grid=moisture_grid,
        slope_grid=slope_grid,
        aspect_grid=aspect_grid,
        cell_size_m=cell_size_m,
        wind_speed_ms=wind_speed_ms,
        wind_from_deg=wind_from_deg
    )

    # Add all ignition points
    for i, j in ignition_points:
        engine.add_ignition(i, j, ignition_time=0.0)

    # Run propagation
    arrival_time = engine.propagate(max_time_minutes=max_time_minutes)

    return arrival_time
