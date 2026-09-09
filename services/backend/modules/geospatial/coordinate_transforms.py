"""Coordinate transformations and CRS utilities for Track C

Handles:
- WGS84 (EPSG:4326) ↔ projected metric CRS transformations
- Wind direction FROM→TO conversion
- Grid coordinate mapping
- Distance calculations (orthogonal Δ, diagonal Δ√2)
"""
import math
from typing import Tuple, Optional
import numpy as np
from pyproj import Transformer, CRS


# Standard metric CRS for Indian region simulations
# UTM Zone 43N covers most of India (72°E - 78°E)
DEFAULT_METRIC_CRS = "EPSG:32643"  # WGS 84 / UTM zone 43N


def get_transformer(
    from_crs: str = "EPSG:4326",
    to_crs: str = DEFAULT_METRIC_CRS
) -> Transformer:
    """Create coordinate transformer

    Args:
        from_crs: Source CRS (default WGS84)
        to_crs: Target CRS (default UTM 43N)

    Returns:
        Transformer object
    """
    return Transformer.from_crs(
        CRS.from_string(from_crs),
        CRS.from_string(to_crs),
        always_xy=True
    )


def wgs84_to_metric(
    lon: float,
    lat: float,
    metric_crs: str = DEFAULT_METRIC_CRS
) -> Tuple[float, float]:
    """Convert WGS84 coordinates to metric CRS

    Args:
        lon: Longitude in degrees
        lat: Latitude in degrees
        metric_crs: Target metric CRS

    Returns:
        (x, y) in meters
    """
    transformer = get_transformer("EPSG:4326", metric_crs)
    x, y = transformer.transform(lon, lat)
    return x, y


def metric_to_wgs84(
    x: float,
    y: float,
    metric_crs: str = DEFAULT_METRIC_CRS
) -> Tuple[float, float]:
    """Convert metric CRS coordinates to WGS84

    Args:
        x: X coordinate in meters
        y: Y coordinate in meters
        metric_crs: Source metric CRS

    Returns:
        (lon, lat) in degrees
    """
    transformer = get_transformer(metric_crs, "EPSG:4326")
    lon, lat = transformer.transform(x, y)
    return lon, lat


def wind_from_to_to(wind_from_deg: float) -> float:
    """Convert meteorological FROM direction to propagation TO direction

    CRITICAL: Meteorological wind reports FROM direction.
    Fire propagates TO the reciprocal direction.

    Args:
        wind_from_deg: Wind FROM direction in degrees (0-360)

    Returns:
        Wind TO direction in degrees (0-360)

    Example:
        >>> wind_from_to_to(270)  # Wind FROM west
        90.0  # Fire propagates TO east
    """
    return (wind_from_deg + 180.0) % 360.0


def bearing_to_cartesian(bearing_deg: float) -> Tuple[float, float]:
    """Convert compass bearing to Cartesian unit vector

    Bearing convention: 0° = North, 90° = East, 180° = South, 270° = West
    Cartesian convention: +X = East, +Y = North

    Args:
        bearing_deg: Bearing in degrees (0-360)

    Returns:
        (dx, dy) unit vector
    """
    # Convert bearing to radians
    bearing_rad = math.radians(bearing_deg)

    # Bearing 0° = North = +Y direction
    # Bearing 90° = East = +X direction
    dx = math.sin(bearing_rad)
    dy = math.cos(bearing_rad)

    return dx, dy


def cartesian_to_bearing(dx: float, dy: float) -> float:
    """Convert Cartesian vector to compass bearing

    Args:
        dx: X component (East direction)
        dy: Y component (North direction)

    Returns:
        Bearing in degrees (0-360)
    """
    bearing_rad = math.atan2(dx, dy)
    bearing_deg = math.degrees(bearing_rad)

    # Normalize to [0, 360)
    if bearing_deg < 0:
        bearing_deg += 360.0

    return bearing_deg


def cell_distance(
    from_i: int,
    from_j: int,
    to_i: int,
    to_j: int,
    cell_size_m: float
) -> float:
    """Calculate distance between grid cells

    CRITICAL: Orthogonal neighbors = cell_size
              Diagonal neighbors = cell_size * √2

    Args:
        from_i: Source row index
        from_j: Source column index
        to_i: Target row index
        to_j: Target column index
        cell_size_m: Grid cell size in meters

    Returns:
        Distance in meters
    """
    di = abs(to_i - from_i)
    dj = abs(to_j - from_j)

    if di == 0 and dj == 1:
        # Horizontal neighbor
        return cell_size_m
    elif di == 1 and dj == 0:
        # Vertical neighbor
        return cell_size_m
    elif di == 1 and dj == 1:
        # Diagonal neighbor
        return cell_size_m * math.sqrt(2.0)
    else:
        # General case (Euclidean)
        return math.sqrt((di * cell_size_m)**2 + (dj * cell_size_m)**2)


def get_8_neighbors(i: int, j: int, rows: int, cols: int):
    """Get 8-neighbor cell indices with bounds checking

    Yields neighbors in order:
    NW  N  NE
    W   X  E
    SW  S  SE

    Args:
        i: Row index
        j: Column index
        rows: Grid height
        cols: Grid width

    Yields:
        (neighbor_i, neighbor_j) tuples
    """
    # 8 directions: N, S, E, W, NE, NW, SE, SW
    directions = [
        (-1, 0),   # N
        (1, 0),    # S
        (0, 1),    # E
        (0, -1),   # W
        (-1, 1),   # NE
        (-1, -1),  # NW
        (1, 1),    # SE
        (1, -1),   # SW
    ]

    for di, dj in directions:
        ni, nj = i + di, j + dj
        if 0 <= ni < rows and 0 <= nj < cols:
            yield ni, nj


def grid_to_metric(
    i: int,
    j: int,
    origin_x: float,
    origin_y: float,
    cell_size_m: float
) -> Tuple[float, float]:
    """Convert grid cell indices to metric coordinates

    Args:
        i: Row index (0 = top)
        j: Column index (0 = left)
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters

    Returns:
        (x, y) in meters (cell center)
    """
    x = origin_x + (j + 0.5) * cell_size_m
    y = origin_y - (i + 0.5) * cell_size_m  # Negative because i=0 is top
    return x, y


def metric_to_grid(
    x: float,
    y: float,
    origin_x: float,
    origin_y: float,
    cell_size_m: float
) -> Tuple[int, int]:
    """Convert metric coordinates to grid cell indices

    Args:
        x: X coordinate in meters
        y: Y coordinate in meters
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters

    Returns:
        (i, j) grid indices
    """
    j = int((x - origin_x) / cell_size_m)
    i = int((origin_y - y) / cell_size_m)  # Negative because i=0 is top
    return i, j


def create_grid_extent(
    center_lon: float,
    center_lat: float,
    width_m: float,
    height_m: float,
    metric_crs: str = DEFAULT_METRIC_CRS
) -> dict:
    """Create grid extent dictionary

    Args:
        center_lon: Center longitude (WGS84)
        center_lat: Center latitude (WGS84)
        width_m: Grid width in meters
        height_m: Grid height in meters
        metric_crs: Metric CRS to use

    Returns:
        Extent dict with origin, bounds, CRS
    """
    # Convert center to metric
    center_x, center_y = wgs84_to_metric(center_lon, center_lat, metric_crs)

    # Calculate origin (top-left corner)
    origin_x = center_x - width_m / 2.0
    origin_y = center_y + height_m / 2.0

    return {
        "crs": metric_crs,
        "origin_x": origin_x,
        "origin_y": origin_y,
        "width_m": width_m,
        "height_m": height_m,
        "center_lon": center_lon,
        "center_lat": center_lat,
        "center_x": center_x,
        "center_y": center_y,
    }
