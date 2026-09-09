"""
Severity (S_h) reference implementation.

Specification: Document 04, Section 8
Operational severity index combining intensity, temporal, and duration components.

Formula: S_h = w_I × I_h + w_T × T_h + w_D × D_h
Range: [0, 1] or None

CRITICAL INVARIANT: Severity ≠ Probability
- S_h measures operational intensity/danger, NOT event likelihood
- Severity deliberately excludes E_h (evidence) to avoid circular dependency

PHASE 5 ITERATION 5: Severity computation.

Design Decisions:
- D13: Simple rate-of-change temporal computation
- D14: Threshold-duration persistence computation
- D15: Prototype intensity thresholds (UNVALIDATED)
- D16: Reweight remaining components when some missing

Missing Semantics:
- All components None → S_h = None (cannot compute)
- Some components None → reweight remaining to sum to 1.0
- Never convert None to 0.0 (missing ≠ zero invariant)

Provenance: ALL threshold and weight values are PROTOTYPE ASSUMPTIONS
Validation Status: UNVALIDATED - NOT scientifically authoritative
Owner: Phase 5 implementation (requires domain expert takeover)
Config Version: 1.0-prototype
"""

from typing import Optional, Dict
import numpy as np

# Numerical constants
EPSILON = 1e-9

# Prototype severity weights (UNVALIDATED)
DEFAULT_SEVERITY_WEIGHTS = {
    'w_I': 0.5,  # Intensity weight
    'w_T': 0.3,  # Temporal weight
    'w_D': 0.2   # Duration weight
}

# Prototype fire intensity thresholds (UNVALIDATED)
DEFAULT_FIRE_INTENSITY_CONFIG = {
    'temp_low': 40.0,    # °C - PROTOTYPE ASSUMPTION
    'temp_high': 100.0,  # °C - PROTOTYPE ASSUMPTION
    'smoke_low': 0.2,    # normalized [0,1] - PROTOTYPE ASSUMPTION
    'smoke_high': 0.8    # normalized [0,1] - PROTOTYPE ASSUMPTION
}

# Prototype flood intensity thresholds (UNVALIDATED)
DEFAULT_FLOOD_INTENSITY_CONFIG = {
    'water_low': 0.5,    # meters - PROTOTYPE ASSUMPTION
    'water_high': 3.0,   # meters - PROTOTYPE ASSUMPTION
    'rain_low': 10.0,    # mm/h - PROTOTYPE ASSUMPTION
    'rain_high': 100.0   # mm/h - PROTOTYPE ASSUMPTION
}

# Prototype temporal computation parameters (UNVALIDATED)
DEFAULT_TEMPORAL_CONFIG = {
    'max_temp_rate': 10.0 / 60.0,    # °C/s (10°C/min) - PROTOTYPE ASSUMPTION
    'max_smoke_rate': 0.5 / 60.0,     # units/s - PROTOTYPE ASSUMPTION
    'max_water_rate': 0.5 / 60.0,     # m/s (0.5m/min) - PROTOTYPE ASSUMPTION
    'max_rain_rate': 100.0,           # mm/h - PROTOTYPE ASSUMPTION
    'max_age_seconds': 300.0          # seconds (5 min) - PROTOTYPE ASSUMPTION
}

# Prototype duration computation parameters (UNVALIDATED)
DEFAULT_DURATION_CONFIG = {
    'max_duration_seconds': 3600.0,   # seconds (1 hour) - PROTOTYPE ASSUMPTION
    'fire_temp_threshold': 50.0,      # °C - PROTOTYPE ASSUMPTION
    'fire_smoke_threshold': 0.3,      # normalized - PROTOTYPE ASSUMPTION
    'flood_water_threshold': 1.0,     # meters - PROTOTYPE ASSUMPTION
    'flood_rain_threshold': 50.0      # mm/h - PROTOTYPE ASSUMPTION
}


def compute_severity(
    i_h: Optional[float],
    t_h: Optional[float],
    d_h: Optional[float],
    weights: Optional[Dict[str, float]] = None,
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute severity from components with reweighting.

    Specification: Document 04, Section 8.1
    Decision: D16 (component reweighting strategy)

    Args:
        i_h: Intensity component [0, 1] or None
        t_h: Temporal component [0, 1] or None
        d_h: Duration component [0, 1] or None
        weights: {'w_I': float, 'w_T': float, 'w_D': float} or None for defaults
        epsilon: Zero-division guard

    Returns:
        S_h in [0, 1] or None

    Formula (all components available):
        S_h = w_I × I_h + w_T × T_h + w_D × D_h

    Missing Semantics (D16):
        - All None → returns None (cannot compute)
        - Some None → reweight remaining to sum to 1.0
        - Never converts None to 0.0 (missing ≠ zero)

    Preserves Invariants:
        - Missing ≠ zero
        - Severity ≠ probability
        - Multi-hazard independence
        - Range [0, 1] for non-None results

    Examples:
        >>> compute_severity(0.8, 0.5, 0.3)  # All available
        0.59  # 0.5*0.8 + 0.3*0.5 + 0.2*0.3

        >>> compute_severity(0.8, None, 0.3)  # Temporal missing
        0.64286  # Reweight: (0.5*0.8 + 0.2*0.3) / (0.5+0.2)

        >>> compute_severity(None, None, None)  # All missing
        None

    Provenance: Default weights are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED
    """
    if weights is None:
        weights = DEFAULT_SEVERITY_WEIGHTS

    # Build component list with weights
    components = [
        (i_h, weights['w_I']),
        (t_h, weights['w_T']),
        (d_h, weights['w_D'])
    ]

    # Filter to available components
    available = [(val, w) for val, w in components if val is not None]

    # All missing → None (cannot compute)
    if len(available) == 0:
        return None

    # Sum available weights for renormalization
    total_weight = sum(w for _, w in available)

    # Guard against invalid weight configuration
    if total_weight < epsilon:
        return None

    # Weighted sum with renormalization
    s_h = sum(val * w for val, w in available) / total_weight

    # Clamp to [0, 1] for numerical safety
    return max(0.0, min(1.0, s_h))


def compute_fire_intensity(
    temperature: Optional[float],
    smoke: Optional[float],
    config: Optional[Dict[str, float]] = None
) -> Optional[float]:
    """
    Compute fire intensity from temperature and smoke sensors.

    Specification: Document 04, Section 8 (intensity component)
    Decision: D15 (prototype intensity thresholds)

    Args:
        temperature: Temperature reading (°C) or None
        smoke: Smoke density reading (normalized [0,1]) or None
        config: Intensity threshold configuration or None for defaults

    Returns:
        I_h in [0, 1] or None

    Temperature Mapping (PROTOTYPE):
        - < temp_low (40°C): I_temp = 0.0
        - temp_low to temp_high (40-100°C): linear interpolation
        - > temp_high (100°C): I_temp = 1.0

    Smoke Mapping (PROTOTYPE):
        - < smoke_low (0.2): I_smoke = 0.0
        - smoke_low to smoke_high (0.2-0.8): linear interpolation
        - > smoke_high (0.8): I_smoke = 1.0

    Combined:
        I_h = max(I_temp, I_smoke)

    Missing Handling:
        - Both None → returns None
        - One None → uses the other
        - Missing ≠ zero preserved

    Examples:
        >>> compute_fire_intensity(70.0, 0.5)
        0.5  # max((70-40)/60, (0.5-0.2)/0.6) = max(0.5, 0.5)

        >>> compute_fire_intensity(None, 0.6)
        0.6667  # (0.6-0.2)/0.6, temperature missing

        >>> compute_fire_intensity(None, None)
        None

    Provenance: ALL thresholds are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED - NOT scientifically authoritative
    Owner: Phase 5 implementation (requires domain expert takeover)
    Units: temperature (°C), smoke (normalized [0,1])
    Valid Ranges: temp_low < temp_high, 0 ≤ smoke_low < smoke_high ≤ 1
    Config Version: 1.0-prototype
    """
    if config is None:
        config = DEFAULT_FIRE_INTENSITY_CONFIG

    temp_low = config['temp_low']
    temp_high = config['temp_high']
    smoke_low = config['smoke_low']
    smoke_high = config['smoke_high']

    intensities = []

    # Temperature intensity
    if temperature is not None:
        if temperature <= temp_low:
            i_temp = 0.0
        elif temperature >= temp_high:
            i_temp = 1.0
        else:
            i_temp = (temperature - temp_low) / (temp_high - temp_low)
        intensities.append(i_temp)

    # Smoke intensity
    if smoke is not None:
        if smoke <= smoke_low:
            i_smoke = 0.0
        elif smoke >= smoke_high:
            i_smoke = 1.0
        else:
            i_smoke = (smoke - smoke_low) / (smoke_high - smoke_low)
        intensities.append(i_smoke)

    # Combined: max of available sensors
    if len(intensities) == 0:
        return None  # Both missing

    return max(intensities)


def compute_flood_intensity(
    water_level: Optional[float],
    rainfall: Optional[float],
    config: Optional[Dict[str, float]] = None
) -> Optional[float]:
    """
    Compute flood intensity from water level and rainfall sensors.

    Specification: Document 04, Section 8 (intensity component)
    Decision: D15 (prototype intensity thresholds)

    Args:
        water_level: Water level reading (meters) or None
        rainfall: Rainfall rate (mm/h) or None
        config: Intensity threshold configuration or None for defaults

    Returns:
        I_h in [0, 1] or None

    Water Level Mapping (PROTOTYPE):
        - < water_low (0.5m): I_water = 0.0
        - water_low to water_high (0.5-3.0m): linear interpolation
        - > water_high (3.0m): I_water = 1.0

    Rainfall Mapping (PROTOTYPE):
        - < rain_low (10mm/h): I_rain = 0.0
        - rain_low to rain_high (10-100mm/h): linear interpolation
        - > rain_high (100mm/h): I_rain = 1.0

    Combined:
        I_h = max(I_water, I_rain)

    Missing Handling:
        - Both None → returns None
        - One None → uses the other
        - Missing ≠ zero preserved

    Examples:
        >>> compute_flood_intensity(1.5, 50.0)
        0.4444  # max((1.5-0.5)/2.5, (50-10)/90)

        >>> compute_flood_intensity(2.0, None)
        0.6  # (2.0-0.5)/2.5, rainfall missing

        >>> compute_flood_intensity(None, None)
        None

    Provenance: ALL thresholds are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED - NOT scientifically authoritative
    Owner: Phase 5 implementation (requires domain expert takeover)
    Units: water_level (meters), rainfall (mm/h)
    Valid Ranges: water_low < water_high, rain_low < rain_high
    Config Version: 1.0-prototype
    """
    if config is None:
        config = DEFAULT_FLOOD_INTENSITY_CONFIG

    water_low = config['water_low']
    water_high = config['water_high']
    rain_low = config['rain_low']
    rain_high = config['rain_high']

    intensities = []

    # Water level intensity
    if water_level is not None:
        if water_level <= water_low:
            i_water = 0.0
        elif water_level >= water_high:
            i_water = 1.0
        else:
            i_water = (water_level - water_low) / (water_high - water_low)
        intensities.append(i_water)

    # Rainfall intensity
    if rainfall is not None:
        if rainfall <= rain_low:
            i_rain = 0.0
        elif rainfall >= rain_high:
            i_rain = 1.0
        else:
            i_rain = (rainfall - rain_low) / (rain_high - rain_low)
        intensities.append(i_rain)

    # Combined: max of available sensors
    if len(intensities) == 0:
        return None  # Both missing

    return max(intensities)


def compute_temporal(
    current: Optional[float],
    previous: Optional[float],
    time_delta_seconds: Optional[float],
    max_rate_per_second: float,
    max_age_seconds: Optional[float] = None
) -> Optional[float]:
    """
    Compute temporal escalation from rate of change.

    Specification: Document 04, Section 8 (temporal component)
    Decision: D13 (simple rate-of-change computation)

    Args:
        current: Current sensor value (hazard-specific units)
        previous: Previous sensor value (same units as current)
        time_delta_seconds: Time elapsed between measurements (seconds)
        max_rate_per_second: Maximum rate for normalization (units/second)
        max_age_seconds: Maximum age before data considered stale (seconds, optional)

    Returns:
        T_h in [0, 1] or None

    Formula:
        rate = abs(current - previous) / time_delta_seconds
        T_h = min(rate / max_rate_per_second, 1.0)

    Missing/Edge Cases:
        - current is None → T_h = None
        - previous is None → T_h = None (cannot compute rate)
        - time_delta_seconds is None → T_h = None
        - time_delta_seconds <= 0 → T_h = 0.0 (no time elapsed)
        - time_delta_seconds > max_age_seconds → T_h = 0.0 (data too stale)

    Examples:
        >>> compute_temporal(70.0, 60.0, 60.0, 0.167)  # 10°C/min rate
        1.0  # abs(70-60)/60 / 0.167 = 1.0

        >>> compute_temporal(65.0, 60.0, 120.0, 0.167)  # Slower rate
        0.25  # abs(65-60)/120 / 0.167

        >>> compute_temporal(None, 60.0, 60.0, 0.167)
        None  # Current missing

    Provenance: max_rate values are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED - NOT scientifically authoritative
    Owner: Phase 5 implementation (requires domain expert takeover)
    Units: hazard-specific (°C, meters, normalized)
    Config Version: 1.0-prototype
    """
    # Missing inputs
    if current is None or previous is None or time_delta_seconds is None:
        return None

    # Edge case: no time elapsed
    if time_delta_seconds <= 0:
        return 0.0

    # Edge case: data too stale
    if max_age_seconds is not None and time_delta_seconds > max_age_seconds:
        return 0.0

    # Compute rate
    rate = abs(current - previous) / time_delta_seconds

    # Normalize to [0, 1]
    t_h = min(rate / max_rate_per_second, 1.0)

    return t_h


def compute_duration(
    above_threshold_seconds: Optional[float],
    max_duration_seconds: float
) -> Optional[float]:
    """
    Compute duration component from time above threshold.

    Specification: Document 04, Section 8 (duration component)
    Decision: D14 (threshold-duration computation)

    Args:
        above_threshold_seconds: Total time conditions above threshold (seconds)
        max_duration_seconds: Maximum duration for normalization (seconds)

    Returns:
        D_h in [0, 1] or None

    Formula:
        D_h = min(above_threshold_seconds / max_duration_seconds, 1.0)

    Missing/Edge Cases:
        - above_threshold_seconds is None → D_h = None (no history)
        - above_threshold_seconds == 0 → D_h = 0.0 (no time above threshold)
        - above_threshold_seconds < 0 → ValueError (invalid input)
        - max_duration_seconds <= 0 → ValueError (invalid config)

    Examples:
        >>> compute_duration(1800.0, 3600.0)  # 30 minutes of 1 hour
        0.5

        >>> compute_duration(5400.0, 3600.0)  # 90 minutes (exceeds max)
        1.0

        >>> compute_duration(0.0, 3600.0)
        0.0

        >>> compute_duration(None, 3600.0)
        None

    Provenance: max_duration_seconds is a PROTOTYPE ASSUMPTION
    Validation Status: UNVALIDATED - NOT scientifically authoritative
    Owner: Phase 5 implementation (requires domain expert takeover)
    Units: seconds
    Config Version: 1.0-prototype
    """
    # Validate configuration
    if max_duration_seconds <= 0:
        raise ValueError(f"max_duration_seconds must be positive, got {max_duration_seconds}")

    # Missing input
    if above_threshold_seconds is None:
        return None

    # Validate input
    if above_threshold_seconds < 0:
        raise ValueError(f"above_threshold_seconds must be non-negative, got {above_threshold_seconds}")

    # Normalize to [0, 1]
    d_h = min(above_threshold_seconds / max_duration_seconds, 1.0)

    return d_h


def validate_severity_weights(
    weights: Dict[str, float],
    epsilon: float = EPSILON
) -> bool:
    """
    Validate severity weight configuration.

    Args:
        weights: {'w_I': float, 'w_T': float, 'w_D': float}
        epsilon: Tolerance for sum-to-one constraint

    Returns:
        True if valid, False otherwise

    Validation Rules:
        - All weights present: w_I, w_T, w_D
        - All weights in [0, 1]
        - Weights sum to 1.0 ± epsilon

    Examples:
        >>> validate_severity_weights({'w_I': 0.5, 'w_T': 0.3, 'w_D': 0.2})
        True

        >>> validate_severity_weights({'w_I': 0.6, 'w_T': 0.3, 'w_D': 0.2})
        False  # Sum != 1.0

        >>> validate_severity_weights({'w_I': -0.1, 'w_T': 0.6, 'w_D': 0.5})
        False  # Negative weight
    """
    required_keys = {'w_I', 'w_T', 'w_D'}

    # Check all keys present
    if set(weights.keys()) != required_keys:
        return False

    # Check all weights in [0, 1]
    for w in weights.values():
        if w < 0 or w > 1:
            return False

    # Check sum to 1.0 ± epsilon
    total = weights['w_I'] + weights['w_T'] + weights['w_D']
    if abs(total - 1.0) > epsilon:
        return False

    return True
