"""Terrain processing for Track C fire spread simulation

Handles:
- DEM (Digital Elevation Model) grid representation
- Slope and aspect computation via central differences
- Terrain gradient calculations
"""
import math
from typing import Tuple, Optional
import numpy as np


def compute_slope_aspect(
    dem: np.ndarray,
    cell_size_m: float,
    nodata_value: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute slope and aspect from DEM using central differences

    CRITICAL: Uses central difference method for gradient computation:
    ∂z/∂x = (z[i,j+1] - z[i,j-1]) / (2*Δx)
    ∂z/∂y = (z[i+1,j] - z[i-1,j]) / (2*Δy)

    Args:
        dem: Digital Elevation Model array (rows, cols) in meters
        cell_size_m: Grid cell size in meters
        nodata_value: NoData value to mask (optional)

    Returns:
        (slope, aspect) arrays
        - slope: radians, 0 = flat, π/2 = vertical
        - aspect: radians, 0 = North, π/2 = East, π = South, 3π/2 = West
                  -1 for flat cells (undefined aspect)
    """
    rows, cols = dem.shape

    # Initialize output arrays
    slope = np.zeros_like(dem, dtype=np.float32)
    aspect = np.full_like(dem, -1.0, dtype=np.float32)  # -1 = undefined

    # Mask nodata cells
    if nodata_value is not None:
        valid_mask = dem != nodata_value
    else:
        valid_mask = np.ones(dem.shape, dtype=bool)

    # Compute gradients using central differences
    # For interior cells, use central difference
    # For edge cells, use forward/backward difference

    for i in range(rows):
        for j in range(cols):
            if not valid_mask[i, j]:
                continue

            # Gradient in X direction (East)
            if j == 0:
                # Left edge: forward difference
                if j + 1 < cols and valid_mask[i, j + 1]:
                    dz_dx = (dem[i, j + 1] - dem[i, j]) / cell_size_m
                else:
                    dz_dx = 0.0
            elif j == cols - 1:
                # Right edge: backward difference
                if valid_mask[i, j - 1]:
                    dz_dx = (dem[i, j] - dem[i, j - 1]) / cell_size_m
                else:
                    dz_dx = 0.0
            else:
                # Interior: central difference
                if valid_mask[i, j - 1] and valid_mask[i, j + 1]:
                    dz_dx = (dem[i, j + 1] - dem[i, j - 1]) / (2.0 * cell_size_m)
                else:
                    dz_dx = 0.0

            # Gradient in Y direction (North)
            # Note: i=0 is top, increasing i goes down (south)
            if i == 0:
                # Top edge: forward difference (going down)
                if i + 1 < rows and valid_mask[i + 1, j]:
                    dz_dy = (dem[i, j] - dem[i + 1, j]) / cell_size_m
                else:
                    dz_dy = 0.0
            elif i == rows - 1:
                # Bottom edge: backward difference
                if valid_mask[i - 1, j]:
                    dz_dy = (dem[i - 1, j] - dem[i, j]) / cell_size_m
                else:
                    dz_dy = 0.0
            else:
                # Interior: central difference
                if valid_mask[i - 1, j] and valid_mask[i + 1, j]:
                    dz_dy = (dem[i - 1, j] - dem[i + 1, j]) / (2.0 * cell_size_m)
                else:
                    dz_dy = 0.0

            # Compute slope (radians)
            gradient_magnitude = math.sqrt(dz_dx**2 + dz_dy**2)
            slope[i, j] = math.atan(gradient_magnitude)

            # Compute aspect (radians)
            if gradient_magnitude > 1e-6:  # Not flat
                # Aspect is direction of maximum uphill slope
                # atan2(dz_dy, dz_dx) gives direction of gradient
                aspect_rad = math.atan2(dz_dx, dz_dy)

                # Normalize to [0, 2π)
                if aspect_rad < 0:
                    aspect_rad += 2 * math.pi

                aspect[i, j] = aspect_rad
            else:
                # Flat cell: aspect undefined
                aspect[i, j] = -1.0

    return slope, aspect


def compute_slope_aspect_vectorized(
    dem: np.ndarray,
    cell_size_m: float,
    nodata_value: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorized slope/aspect computation (faster for large DEMs)

    Uses numpy operations for performance.

    Args:
        dem: Digital Elevation Model array (rows, cols) in meters
        cell_size_m: Grid cell size in meters
        nodata_value: NoData value to mask (optional)

    Returns:
        (slope, aspect) arrays (same format as compute_slope_aspect)
    """
    rows, cols = dem.shape

    # Mask nodata
    if nodata_value is not None:
        valid_mask = dem != nodata_value
        dem_masked = np.where(valid_mask, dem, np.nan)
    else:
        dem_masked = dem.astype(np.float32)

    # Compute gradients using numpy gradient
    # numpy.gradient uses central differences for interior, one-sided for edges
    dz_dy, dz_dx = np.gradient(dem_masked, cell_size_m)

    # Handle NaN from nodata
    dz_dx = np.nan_to_num(dz_dx, nan=0.0)
    dz_dy = np.nan_to_num(dz_dy, nan=0.0)

    # Note: numpy gradient convention has i=0 at top, increasing downward
    # So dz_dy points south (downhill). Negate to get north (uphill)
    dz_dy = -dz_dy

    # Compute slope
    gradient_magnitude = np.sqrt(dz_dx**2 + dz_dy**2)
    slope = np.arctan(gradient_magnitude)

    # Compute aspect
    aspect = np.arctan2(dz_dx, dz_dy)

    # Normalize aspect to [0, 2π)
    aspect = np.where(aspect < 0, aspect + 2 * np.pi, aspect)

    # Mark flat cells with aspect = -1
    flat_mask = gradient_magnitude < 1e-6
    aspect = np.where(flat_mask, -1.0, aspect)

    # Mask invalid cells
    if nodata_value is not None:
        slope = np.where(valid_mask, slope, 0.0)
        aspect = np.where(valid_mask, aspect, -1.0)

    return slope, aspect


def slope_factor_for_direction(
    slope_rad: float,
    aspect_rad: float,
    propagation_bearing_rad: float
) -> float:
    """Compute slope influence factor for a propagation direction

    Fire spreads faster uphill, slower downhill.

    Args:
        slope_rad: Terrain slope in radians (0 = flat)
        aspect_rad: Uphill direction in radians (-1 = flat/undefined)
        propagation_bearing_rad: Fire propagation bearing in radians

    Returns:
        Slope factor (1.0 = no effect, >1 = uphill acceleration, <1 = downhill)
    """
    if slope_rad < 1e-6 or aspect_rad < 0:
        # Flat terrain or undefined aspect: no slope effect
        return 1.0

    # Angle between propagation direction and uphill direction
    angle_diff = propagation_bearing_rad - aspect_rad

    # Normalize to [-π, π]
    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    while angle_diff < -math.pi:
        angle_diff += 2 * math.pi

    # Projection: cos(angle_diff)
    # = 1.0 when propagating directly uphill
    # = 0.0 when propagating across slope
    # = -1.0 when propagating directly downhill
    projection = math.cos(angle_diff)

    # Slope effect: uphill accelerates, downhill suppresses
    # Factor form: 1 + k * tan(slope) * projection
    # k is calibrated coefficient (typically 2.0 - 3.0)
    k = 3.0
    slope_effect = k * math.tan(slope_rad) * projection

    # Factor bounded to prevent negative ROS
    factor = 1.0 + slope_effect
    return max(0.1, factor)  # Minimum 0.1 to prevent zero ROS


def create_synthetic_dem(
    rows: int,
    cols: int,
    cell_size_m: float,
    base_elevation_m: float = 100.0,
    slope_deg: float = 5.0,
    slope_direction_deg: float = 45.0
) -> np.ndarray:
    """Create synthetic DEM for testing

    Args:
        rows: Number of rows
        cols: Number of columns
        cell_size_m: Cell size in meters
        base_elevation_m: Base elevation in meters
        slope_deg: Uniform slope in degrees
        slope_direction_deg: Direction of slope (0=N, 90=E, 180=S, 270=W)

    Returns:
        DEM array
    """
    dem = np.zeros((rows, cols), dtype=np.float32)

    # Convert slope to rise/run
    slope_rad = math.radians(slope_deg)
    rise_per_cell = cell_size_m * math.tan(slope_rad)

    # Slope direction components
    direction_rad = math.radians(slope_direction_deg)
    dx = math.sin(direction_rad)  # East component
    dy = math.cos(direction_rad)  # North component

    # Apply slope across grid
    for i in range(rows):
        for j in range(cols):
            # Distance from top-left corner in slope direction
            distance_x = j * cell_size_m
            distance_y = i * cell_size_m

            # Elevation change
            elevation_change = (distance_x * dx + distance_y * dy) * math.tan(slope_rad)

            dem[i, j] = base_elevation_m + elevation_change

    return dem


def create_flat_dem(
    rows: int,
    cols: int,
    elevation_m: float = 100.0
) -> np.ndarray:
    """Create flat DEM for testing

    Args:
        rows: Number of rows
        cols: Number of columns
        elevation_m: Constant elevation

    Returns:
        Flat DEM array
    """
    return np.full((rows, cols), elevation_m, dtype=np.float32)
