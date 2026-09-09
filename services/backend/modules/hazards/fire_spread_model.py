"""Fire spread model for Track C

Implements directional Rate of Spread (ROS) computation based on:
- Fuel type and base ROS
- Moisture suppression factor
- Wind forcing (FROM→TO conversion)
- Slope forcing
- Combined wind+slope directional anisotropy
"""
import math
from typing import Tuple, Optional
from enum import Enum
import numpy as np


class FuelType(Enum):
    """Categorical fuel classes for V1 simplified model"""
    NONBURNABLE = 0
    GRASS = 1
    BRUSH = 2
    FOREST = 3
    WATER = 4


# Base ROS per fuel type (m/min) under reference conditions
# These are simplified prototype values
FUEL_BASE_ROS = {
    FuelType.NONBURNABLE: 0.0,
    FuelType.GRASS: 3.0,        # Fast-spreading grassland
    FuelType.BRUSH: 1.5,        # Medium brush/shrubland
    FuelType.FOREST: 0.8,       # Slower forest floor
    FuelType.WATER: 0.0,
}


def get_base_ros(fuel_type: FuelType) -> float:
    """Get base ROS for fuel type

    Args:
        fuel_type: Fuel classification

    Returns:
        Base ROS in m/min
    """
    return FUEL_BASE_ROS.get(fuel_type, 0.0)


def moisture_factor(moisture_index: float) -> float:
    """Compute moisture suppression factor

    CRITICAL: This is a normalized moisture INDEX/proxy, not literal fuel moisture.

    Args:
        moisture_index: Normalized moisture [0, 1]
                       0 = very dry (maximum spread)
                       1 = very wet (suppressed spread)

    Returns:
        Moisture factor F_M ∈ (0, 1]
        Lower moisture → higher factor → faster spread
    """
    # Inverse relationship: dry conditions increase spread
    # F_M = 1.0 - 0.8 * moisture_index
    # Bounded to (0.2, 1.0] to prevent complete suppression
    factor = 1.0 - 0.8 * moisture_index
    return max(0.2, min(1.0, factor))


def wind_forcing_vector(
    wind_speed_ms: float,
    wind_from_deg: float,
    wind_adjustment_factor: float = 0.4
) -> Tuple[float, float, float]:
    """Compute wind forcing vector

    CRITICAL: Wind FROM direction must be converted to TO direction.
    θ_TO = (θ_FROM + 180) % 360

    Args:
        wind_speed_ms: Wind speed in m/s
        wind_from_deg: Meteorological FROM direction (0-360°)
        wind_adjustment_factor: Midflame adjustment (default 0.4)

    Returns:
        (magnitude, direction_rad, (vx, vy))
        - magnitude: Effective wind forcing strength
        - direction_rad: TO direction in radians
        - (vx, vy): Unit vector components
    """
    # CRITICAL: Convert FROM to TO
    wind_to_deg = (wind_from_deg + 180.0) % 360.0

    # Midflame wind adjustment
    u_mid = wind_speed_ms * wind_adjustment_factor

    # Wind forcing magnitude
    # Calibration coefficient (typical 2.0-3.0)
    k_wind = 2.5
    magnitude = k_wind * u_mid

    # Direction vector
    direction_rad = math.radians(wind_to_deg)
    vx = math.sin(direction_rad)  # East component
    vy = math.cos(direction_rad)  # North component

    return magnitude, direction_rad, (vx, vy)


def slope_forcing_vector(
    slope_rad: float,
    aspect_rad: float
) -> Tuple[float, float, Tuple[float, float]]:
    """Compute slope forcing vector

    Args:
        slope_rad: Terrain slope in radians
        aspect_rad: Uphill direction in radians (-1 = flat/undefined)

    Returns:
        (magnitude, direction_rad, (vx, vy))
        - magnitude: Effective slope forcing strength
        - direction_rad: Uphill direction in radians
        - (vx, vy): Unit vector components (zero if flat)
    """
    if slope_rad < 1e-6 or aspect_rad < 0:
        # Flat or undefined: no slope forcing
        return 0.0, 0.0, (0.0, 0.0)

    # Slope forcing magnitude
    # Calibration coefficient (typical 2.0-4.0)
    k_slope = 3.0
    magnitude = k_slope * math.tan(slope_rad)

    # Direction vector (uphill)
    vx = math.sin(aspect_rad)  # East component
    vy = math.cos(aspect_rad)  # North component

    return magnitude, aspect_rad, (vx, vy)


def combined_forcing(
    wind_mag: float,
    wind_vec: Tuple[float, float],
    slope_mag: float,
    slope_vec: Tuple[float, float]
) -> Tuple[float, float]:
    """Combine wind and slope forcing vectors

    V_eff = V_wind + V_slope

    Args:
        wind_mag: Wind forcing magnitude
        wind_vec: Wind unit vector (vx, vy)
        slope_mag: Slope forcing magnitude
        slope_vec: Slope unit vector (vx, vy)

    Returns:
        (U_eff, θ_eff)
        - U_eff: Combined forcing strength
        - θ_eff: Effective head-fire direction (radians)
    """
    # Vector addition
    v_wind_x = wind_mag * wind_vec[0]
    v_wind_y = wind_mag * wind_vec[1]

    v_slope_x = slope_mag * slope_vec[0]
    v_slope_y = slope_mag * slope_vec[1]

    v_eff_x = v_wind_x + v_slope_x
    v_eff_y = v_wind_y + v_slope_y

    # Magnitude and direction
    u_eff = math.sqrt(v_eff_x**2 + v_eff_y**2)
    theta_eff = math.atan2(v_eff_x, v_eff_y)

    return u_eff, theta_eff


def directional_factor(
    propagation_bearing_rad: float,
    head_direction_rad: float,
    forcing_magnitude: float,
    max_lb_ratio: float = 3.0
) -> float:
    """Compute directional spread factor (elliptical anisotropy)

    Args:
        propagation_bearing_rad: Direction of spread attempt (radians)
        head_direction_rad: Head-fire direction from forcing (radians)
        forcing_magnitude: Combined forcing strength
        max_lb_ratio: Maximum length/breadth ratio for ellipse

    Returns:
        Directional factor (1.0 = no wind/slope, >1 = head fire, <1 = flanking)
    """
    if forcing_magnitude < 1e-6:
        # No forcing: isotropic spread
        return 1.0

    # Angle between propagation and head-fire direction
    angle_diff = propagation_bearing_rad - head_direction_rad

    # Normalize to [-π, π]
    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    while angle_diff < -math.pi:
        angle_diff += 2 * math.pi

    # Elliptical anisotropy
    # Eccentricity based on forcing magnitude
    # Map forcing to length/breadth ratio
    lb_ratio = 1.0 + (max_lb_ratio - 1.0) * math.tanh(forcing_magnitude / 3.0)

    # Projection factor
    cos_angle = math.cos(angle_diff)

    # Ellipse factor: head fire faster, backing fire slower
    # Simplified model: factor = (1 + cos_angle) / 2 * (lb_ratio - 1) + 1
    if cos_angle >= 0:
        # Forward quadrants (head and flanks)
        factor = 1.0 + (lb_ratio - 1.0) * cos_angle
    else:
        # Backward quadrants (backing fire)
        # Suppression factor for backing
        factor = 1.0 + 0.5 * (lb_ratio - 1.0) * cos_angle

    return max(0.1, factor)  # Bounded to prevent zero


def compute_ros(
    fuel_type: FuelType,
    moisture_index: float,
    wind_speed_ms: float,
    wind_from_deg: float,
    slope_rad: float,
    aspect_rad: float,
    propagation_bearing_deg: float
) -> float:
    """Compute directional Rate of Spread

    Full ROS computation chain:
    1. Base ROS from fuel type
    2. Moisture suppression
    3. Wind forcing vector
    4. Slope forcing vector
    5. Combined forcing
    6. Directional factor
    7. Final ROS

    Args:
        fuel_type: Fuel classification
        moisture_index: Normalized moisture [0, 1]
        wind_speed_ms: Wind speed (m/s)
        wind_from_deg: Wind FROM direction (degrees)
        slope_rad: Terrain slope (radians)
        aspect_rad: Uphill direction (radians, -1 = flat)
        propagation_bearing_deg: Fire propagation direction (degrees)

    Returns:
        ROS in m/min
    """
    # 1. Base ROS
    ros_base = get_base_ros(fuel_type)
    if ros_base == 0.0:
        return 0.0  # Non-burnable

    # 2. Moisture factor
    f_m = moisture_factor(moisture_index)
    ros_moisture = ros_base * f_m

    # 3. Wind forcing
    wind_mag, wind_dir, wind_vec = wind_forcing_vector(wind_speed_ms, wind_from_deg)

    # 4. Slope forcing
    slope_mag, slope_dir, slope_vec = slope_forcing_vector(slope_rad, aspect_rad)

    # 5. Combined forcing
    u_eff, theta_eff = combined_forcing(wind_mag, wind_vec, slope_mag, slope_vec)

    # 6. Directional factor
    propagation_rad = math.radians(propagation_bearing_deg)
    f_dir = directional_factor(propagation_rad, theta_eff, u_eff)

    # 7. Final ROS
    ros = ros_moisture * f_dir

    return max(0.0, ros)


def ros_to_neighbor(
    from_i: int,
    from_j: int,
    to_i: int,
    to_j: int,
    fuel_grid: np.ndarray,
    moisture_grid: np.ndarray,
    slope_grid: np.ndarray,
    aspect_grid: np.ndarray,
    wind_speed_ms: float,
    wind_from_deg: float
) -> float:
    """Compute ROS from one cell to a neighbor

    Args:
        from_i, from_j: Source cell indices
        to_i, to_j: Target cell indices
        fuel_grid: Fuel type grid (int, FuelType enum values)
        moisture_grid: Moisture index grid [0, 1]
        slope_grid: Slope grid (radians)
        aspect_grid: Aspect grid (radians, -1 = flat)
        wind_speed_ms: Wind speed (m/s)
        wind_from_deg: Wind FROM direction (degrees)

    Returns:
        ROS in m/min
    """
    # Source cell properties
    fuel_value = int(fuel_grid[from_i, from_j])
    fuel_type = FuelType(fuel_value)

    if fuel_type == FuelType.NONBURNABLE or fuel_type == FuelType.WATER:
        return 0.0

    moisture = float(moisture_grid[from_i, from_j])
    slope = float(slope_grid[from_i, from_j])
    aspect = float(aspect_grid[from_i, from_j])

    # Propagation direction
    di = to_i - from_i
    dj = to_j - from_j

    # Convert cell offset to bearing
    # dj > 0 → East, di > 0 → South (because i=0 is top)
    propagation_rad = math.atan2(dj, -di)  # Negative di because i increases downward
    propagation_deg = math.degrees(propagation_rad)
    if propagation_deg < 0:
        propagation_deg += 360.0

    # Compute ROS
    ros = compute_ros(
        fuel_type=fuel_type,
        moisture_index=moisture,
        wind_speed_ms=wind_speed_ms,
        wind_from_deg=wind_from_deg,
        slope_rad=slope,
        aspect_rad=aspect,
        propagation_bearing_deg=propagation_deg
    )

    return ros
