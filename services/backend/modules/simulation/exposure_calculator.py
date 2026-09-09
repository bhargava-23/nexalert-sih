"""Exposure calculation for Track C

Computes population and infrastructure exposure to fire hazard.

CRITICAL: Exposure is downstream of physical hazard, NOT part of the hazard itself.
Clean hooks for citizen/building data integration.
"""
from typing import List, Dict, Optional, Tuple
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon


def compute_population_exposure(
    fire_geometry: Polygon | MultiPolygon,
    population_grid: np.ndarray,
    origin_x: float,
    origin_y: float,
    cell_size_m: float
) -> dict:
    """Compute population exposure to fire geometry

    Args:
        fire_geometry: Fire hazard geometry
        population_grid: Population density grid (persons per cell)
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters

    Returns:
        Exposure dict with population_at_risk, cells_affected
    """
    if fire_geometry.is_empty:
        return {
            "population_at_risk": 0,
            "cells_affected": 0,
            "population_density_mean": 0.0,
        }

    rows, cols = population_grid.shape
    population_at_risk = 0
    cells_affected = 0
    density_sum = 0.0

    # Check each cell for intersection with fire geometry
    for i in range(rows):
        for j in range(cols):
            # Cell center coordinates
            x = origin_x + (j + 0.5) * cell_size_m
            y = origin_y - (i + 0.5) * cell_size_m

            point = Point(x, y)

            # Check if cell is within fire geometry
            if fire_geometry.contains(point):
                pop = population_grid[i, j]
                if pop > 0:
                    population_at_risk += pop
                    cells_affected += 1
                    density_sum += pop

    mean_density = density_sum / cells_affected if cells_affected > 0 else 0.0

    return {
        "population_at_risk": int(population_at_risk),
        "cells_affected": int(cells_affected),
        "population_density_mean": float(mean_density),
    }


def compute_infrastructure_exposure(
    fire_geometry: Polygon | MultiPolygon,
    infrastructure_points: List[Dict]
) -> dict:
    """Compute infrastructure exposure to fire geometry

    Args:
        fire_geometry: Fire hazard geometry
        infrastructure_points: List of infrastructure dicts with:
            - "lon": Longitude
            - "lat": Latitude
            - "type": Infrastructure type (e.g., "building", "road", "powerline")
            - "id": Unique identifier (optional)

    Returns:
        Exposure dict with structures_threatened, by_type counts
    """
    if fire_geometry.is_empty:
        return {
            "structures_threatened": 0,
            "by_type": {},
            "threatened_ids": [],
        }

    structures_threatened = 0
    by_type: Dict[str, int] = {}
    threatened_ids = []

    for infra in infrastructure_points:
        lon = infra.get("lon")
        lat = infra.get("lat")
        infra_type = infra.get("type", "unknown")
        infra_id = infra.get("id")

        if lon is None or lat is None:
            continue

        # Note: This assumes infrastructure_points are in same CRS as geometry
        # In practice, would need to transform WGS84 → metric CRS first
        point = Point(lon, lat)

        # Check if within fire geometry
        if fire_geometry.contains(point):
            structures_threatened += 1

            # Count by type
            by_type[infra_type] = by_type.get(infra_type, 0) + 1

            # Track threatened IDs
            if infra_id is not None:
                threatened_ids.append(infra_id)

    return {
        "structures_threatened": int(structures_threatened),
        "by_type": by_type,
        "threatened_ids": threatened_ids,
    }


def compute_zone_exposure(
    current_geometry: Polygon | MultiPolygon,
    warning_geometry: Polygon | MultiPolygon,
    projection_geometry: Polygon | MultiPolygon,
    population_grid: np.ndarray,
    infrastructure_points: List[Dict],
    origin_x: float,
    origin_y: float,
    cell_size_m: float
) -> dict:
    """Compute exposure for all three fire zones

    Args:
        current_geometry: Current fire footprint
        warning_geometry: Warning zone footprint
        projection_geometry: Projection zone footprint
        population_grid: Population density grid
        infrastructure_points: Infrastructure locations
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters

    Returns:
        Exposure dict with current/warning/projection sub-dicts
    """
    # Compute population exposure per zone
    current_pop = compute_population_exposure(
        current_geometry, population_grid, origin_x, origin_y, cell_size_m
    )
    warning_pop = compute_population_exposure(
        warning_geometry, population_grid, origin_x, origin_y, cell_size_m
    )
    projection_pop = compute_population_exposure(
        projection_geometry, population_grid, origin_x, origin_y, cell_size_m
    )

    # Compute infrastructure exposure per zone
    current_infra = compute_infrastructure_exposure(current_geometry, infrastructure_points)
    warning_infra = compute_infrastructure_exposure(warning_geometry, infrastructure_points)
    projection_infra = compute_infrastructure_exposure(projection_geometry, infrastructure_points)

    return {
        "current": {
            "population": current_pop,
            "infrastructure": current_infra,
        },
        "warning": {
            "population": warning_pop,
            "infrastructure": warning_infra,
        },
        "projection": {
            "population": projection_pop,
            "infrastructure": projection_infra,
        },
        "total": {
            "population_at_risk": (
                current_pop["population_at_risk"] +
                warning_pop["population_at_risk"] +
                projection_pop["population_at_risk"]
            ),
            "structures_threatened": (
                current_infra["structures_threatened"] +
                warning_infra["structures_threatened"] +
                projection_infra["structures_threatened"]
            ),
        },
    }


def create_synthetic_population_grid(
    rows: int,
    cols: int,
    mean_density: float = 50.0,
    std_density: float = 20.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """Create synthetic population grid for testing

    Args:
        rows: Number of rows
        cols: Number of columns
        mean_density: Mean population density (persons per cell)
        std_density: Standard deviation
        seed: Random seed for reproducibility

    Returns:
        Population grid (persons per cell)
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate random population densities
    population = np.random.normal(mean_density, std_density, size=(rows, cols))

    # Clip to non-negative
    population = np.clip(population, 0, None)

    return population.astype(np.int32)


def create_synthetic_infrastructure(
    num_buildings: int,
    bbox: Tuple[float, float, float, float],
    seed: Optional[int] = None
) -> List[Dict]:
    """Create synthetic infrastructure points for testing

    Args:
        num_buildings: Number of buildings to generate
        bbox: Bounding box (min_x, min_y, max_x, max_y) in meters
        seed: Random seed for reproducibility

    Returns:
        List of infrastructure dicts
    """
    if seed is not None:
        np.random.seed(seed)

    min_x, min_y, max_x, max_y = bbox

    infrastructure = []
    building_types = ["residential", "commercial", "industrial", "public"]

    for i in range(num_buildings):
        x = np.random.uniform(min_x, max_x)
        y = np.random.uniform(min_y, max_y)

        # Note: In actual implementation, would store in metric CRS
        # and transform to WGS84 when needed
        infrastructure.append({
            "id": f"BLDG-{i:04d}",
            "lon": float(x),  # Placeholder: actually metric X
            "lat": float(y),  # Placeholder: actually metric Y
            "type": np.random.choice(building_types),
        })

    return infrastructure


# Hooks for downstream citizen/building data integration

def get_citizens_in_geometry(
    geometry: Polygon | MultiPolygon,
    citizen_database_connection
) -> List[Dict]:
    """Hook for citizen data integration

    PLACEHOLDER: To be implemented when citizen database is available.

    Args:
        geometry: Fire hazard geometry
        citizen_database_connection: Database connection handle

    Returns:
        List of citizen records at risk
    """
    # TODO: Implement citizen database query
    # SELECT * FROM citizens WHERE ST_Within(location, geometry)
    raise NotImplementedError("Citizen database integration not yet implemented")


def get_buildings_in_geometry(
    geometry: Polygon | MultiPolygon,
    building_database_connection
) -> List[Dict]:
    """Hook for building data integration

    PLACEHOLDER: To be implemented when building database is available.

    Args:
        geometry: Fire hazard geometry
        building_database_connection: Database connection handle

    Returns:
        List of building records threatened
    """
    # TODO: Implement building database query
    # SELECT * FROM buildings WHERE ST_Within(centroid, geometry)
    raise NotImplementedError("Building database integration not yet implemented")


def exposure_summary(exposure: dict) -> str:
    """Generate human-readable exposure summary

    Args:
        exposure: Exposure dict from compute_zone_exposure

    Returns:
        Summary string
    """
    total = exposure.get("total", {})
    population = total.get("population_at_risk", 0)
    structures = total.get("structures_threatened", 0)

    current = exposure.get("current", {})
    warning = exposure.get("warning", {})
    projection = exposure.get("projection", {})

    lines = [
        f"Total Exposure:",
        f"  Population at risk: {population:,} people",
        f"  Structures threatened: {structures:,}",
        f"",
        f"By Zone:",
        f"  Current: {current.get('population', {}).get('population_at_risk', 0):,} people, "
        f"{current.get('infrastructure', {}).get('structures_threatened', 0):,} structures",
        f"  Warning: {warning.get('population', {}).get('population_at_risk', 0):,} people, "
        f"{warning.get('infrastructure', {}).get('structures_threatened', 0):,} structures",
        f"  Projection: {projection.get('population', {}).get('population_at_risk', 0):,} people, "
        f"{projection.get('infrastructure', {}).get('structures_threatened', 0):,} structures",
    ]

    return "\n".join(lines)
