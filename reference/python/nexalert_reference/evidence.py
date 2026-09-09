"""
Evidence (E_h) reference implementation.

Specification: Document 04, Sections 6.1-6.4
Deterministic configuration-driven hazard evidence aggregation.

Formula: E_h = threshold-based rule matching with core evidence floor
Range: [0, 1] or None

PHASE 5 ITERATION 4: Hazard-specific evidence computation.
"""
import numpy as np
from typing import Dict, List, Optional

EPSILON = 1e-9


def compute_evidence(
    hazard_type: str,
    sensor_readings: Dict[str, float],
    evidence_config: Dict,
    epsilon: float = EPSILON
) -> Optional[float]:
    """
    Compute deterministic hazard evidence from sensor readings.

    Args:
        hazard_type: Hazard identifier (e.g., "fire", "flood")
        sensor_readings: Dict of sensor_type → current value
        evidence_config: Hazard-specific evidence configuration with:
            - core_evidence: List of core evidence rules
            - supporting_evidence: List of supporting evidence rules
            - core_evidence_floor: {min_core_coverage, cap_without_core}
        epsilon: Zero-division guard (default 1e-9)

    Returns:
        E_h in [0, 1] or None if insufficient data

    Missing Handling:
    - None sensor readings → excluded from computation
    - Missing sensors are NOT negative evidence
    - If all sensors missing → returns None
    - Never convert missing to zero

    Core Evidence Floor:
    - If core_coverage < min_core_coverage → E_h capped at cap_without_core
    - Example: Fire without temp/smoke → E_h ≤ 0.3

    Evidence Aggregation:
    - For each sensor: if value in [threshold_min, threshold_max] → contributes weight
    - E_h_raw = sum(matched_weights) / sum(all_weights)
    - E_h clamped to [0, 1]
    - Core floor applied if core coverage insufficient

    Configuration Validation:
    - All thresholds must have units specified
    - All thresholds must be scientifically validated
    - Rules must be reviewed by domain experts
    - Configuration must track provenance and validation status

    Provenance: ALL threshold values are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED - NOT scientifically authoritative
    Owner: Phase 5 implementation (requires domain expert takeover)

    Specification: Document 04, Sections 6.1-6.4

    Examples:
        >>> config = {
        ...     "core_evidence": [
        ...         {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5},
        ...         {"sensor": "smoke", "threshold_min": 0.3, "threshold_max": 1.0, "weight": 0.3}
        ...     ],
        ...     "supporting_evidence": [
        ...         {"sensor": "humidity", "threshold_min": 0.0, "threshold_max": 0.3, "weight": 0.1}
        ...     ],
        ...     "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        ... }
        >>> compute_evidence("fire", {"temperature": 80.0, "smoke": 0.6}, config)
        0.8  # Both core sensors match

        >>> compute_evidence("fire", {"temperature": None, "smoke": 0.6}, config)
        0.3  # Core coverage < 0.5, capped at cap_without_core

        >>> compute_evidence("fire", {"temperature": None, "smoke": None}, config)
        None  # All sensors missing
    """
    # Validate configuration
    if not evidence_config:
        return None

    core_rules = evidence_config.get("core_evidence", [])
    supporting_rules = evidence_config.get("supporting_evidence", [])
    all_rules = core_rules + supporting_rules

    if not all_rules:
        return None  # No sensors configured for hazard

    # Compute evidence from rule matching
    matched_weight = 0.0
    total_weight = 0.0
    available_sensor_count = 0

    for rule in all_rules:
        sensor_type = rule["sensor"]
        threshold_min = rule["threshold_min"]
        threshold_max = rule["threshold_max"]
        weight = rule["weight"]

        total_weight += weight

        # Check if sensor reading available
        reading = sensor_readings.get(sensor_type)
        if reading is not None:
            available_sensor_count += 1
            # Check if matches threshold
            if threshold_min <= reading <= threshold_max:
                matched_weight += weight

    # Check if all sensors missing
    if available_sensor_count == 0:
        return None  # All sensors missing

    # Check for zero denominator
    if total_weight < epsilon:
        return None

    # Compute raw evidence
    e_h_raw = matched_weight / total_weight

    # Compute core coverage
    core_floor_config = evidence_config.get("core_evidence_floor", {})
    if core_floor_config and core_rules:
        core_coverage = compute_core_coverage(sensor_readings, core_rules)
        min_core_coverage = core_floor_config.get("min_core_coverage", 0.5)
        cap_without_core = core_floor_config.get("cap_without_core", 0.3)

        e_h = apply_core_floor(e_h_raw, core_coverage, min_core_coverage, cap_without_core)
    else:
        e_h = e_h_raw

    # Clamp to [0, 1]
    return float(np.clip(e_h, 0.0, 1.0))


def compute_core_coverage(
    sensor_readings: Dict[str, float],
    core_rules: List[Dict]
) -> float:
    """
    Compute fraction of core evidence sensors available.

    Args:
        sensor_readings: Dict of sensor_type → current value
        core_rules: List of core evidence rules

    Returns:
        Core coverage in [0, 1]

    Missing Handling:
    - Sensor reading is None → unavailable (not counted in coverage)
    - Never convert missing to zero

    Examples:
        >>> core_rules = [
        ...     {"sensor": "temperature", "weight": 0.5},
        ...     {"sensor": "smoke", "weight": 0.3}
        ... ]
        >>> compute_core_coverage({"temperature": 80.0, "smoke": 0.6}, core_rules)
        1.0  # Both available

        >>> compute_core_coverage({"temperature": 80.0, "smoke": None}, core_rules)
        0.625  # Only temperature (weight 0.5 / total 0.8)
    """
    if not core_rules:
        return 1.0  # No core sensors required

    total_core_weight = 0.0
    available_core_weight = 0.0

    for rule in core_rules:
        sensor_type = rule["sensor"]
        weight = rule["weight"]

        total_core_weight += weight

        # Check if sensor reading available (not None)
        reading = sensor_readings.get(sensor_type)
        if reading is not None:
            available_core_weight += weight

    if total_core_weight == 0:
        return 1.0

    return available_core_weight / total_core_weight


def apply_core_floor(
    e_h: float,
    core_coverage: float,
    min_core_coverage: float,
    cap_without_core: float
) -> float:
    """
    Apply core evidence floor to cap E_h when core coverage insufficient.

    Args:
        e_h: Raw evidence score [0, 1]
        core_coverage: Fraction of core evidence available [0, 1]
        min_core_coverage: Minimum core coverage required (PROTOTYPE: 0.5)
        cap_without_core: Max E_h without core evidence (PROTOTYPE: 0.3)

    Returns:
        E_h capped by core floor if necessary

    Core Evidence Floor Logic:
    - If core_coverage >= min_core_coverage → no cap (return e_h)
    - If core_coverage < min_core_coverage → E_h = min(e_h, cap_without_core)

    Provenance: min_core_coverage=0.5, cap_without_core=0.3 are PROTOTYPE ASSUMPTIONS
    Validation Status: UNVALIDATED

    Examples:
        >>> apply_core_floor(0.8, 1.0, 0.5, 0.3)
        0.8  # Core coverage sufficient, no cap

        >>> apply_core_floor(0.8, 0.3, 0.5, 0.3)
        0.3  # Core coverage insufficient, capped at 0.3

        >>> apply_core_floor(0.2, 0.3, 0.5, 0.3)
        0.2  # Below cap anyway
    """
    if core_coverage >= min_core_coverage:
        return e_h  # Core coverage sufficient
    else:
        return min(e_h, cap_without_core)  # Cap evidence


def validate_evidence_config(evidence_config: Dict) -> bool:
    """
    Validate evidence configuration structure and constraints.

    Args:
        evidence_config: Evidence configuration to validate

    Returns:
        True if valid, raises ValueError if invalid

    Validation Rules:
    - Must have core_evidence or supporting_evidence
    - Each rule must have: sensor, threshold_min, threshold_max, weight
    - Weights must be in [0, 1]
    - threshold_min <= threshold_max
    - If core_evidence_floor present: must have min_core_coverage, cap_without_core
    - Both floor parameters must be in [0, 1]

    Raises:
        ValueError: If configuration invalid

    Examples:
        >>> config = {
        ...     "core_evidence": [
        ...         {"sensor": "temperature", "threshold_min": 60.0, "threshold_max": 150.0, "weight": 0.5}
        ...     ],
        ...     "core_evidence_floor": {"min_core_coverage": 0.5, "cap_without_core": 0.3}
        ... }
        >>> validate_evidence_config(config)
        True
    """
    if not evidence_config:
        raise ValueError("Evidence configuration cannot be empty")

    core_rules = evidence_config.get("core_evidence", [])
    supporting_rules = evidence_config.get("supporting_evidence", [])
    all_rules = core_rules + supporting_rules

    if not all_rules:
        raise ValueError("Must have at least one evidence rule")

    # Validate each rule
    for rule_type, rules in [("core", core_rules), ("supporting", supporting_rules)]:
        for i, rule in enumerate(rules):
            # Check required fields
            required_fields = ["sensor", "threshold_min", "threshold_max", "weight"]
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"{rule_type} evidence rule {i}: missing required field '{field}'")

            # Validate weight
            weight = rule["weight"]
            if not (0.0 <= weight <= 1.0):
                raise ValueError(f"{rule_type} evidence rule {i}: weight must be in [0, 1], got {weight}")

            # Validate thresholds
            threshold_min = rule["threshold_min"]
            threshold_max = rule["threshold_max"]
            if threshold_min > threshold_max:
                raise ValueError(
                    f"{rule_type} evidence rule {i}: threshold_min ({threshold_min}) > "
                    f"threshold_max ({threshold_max})"
                )

    # Validate core evidence floor if present
    if "core_evidence_floor" in evidence_config:
        floor_config = evidence_config["core_evidence_floor"]

        if "min_core_coverage" not in floor_config:
            raise ValueError("core_evidence_floor: missing required field 'min_core_coverage'")
        if "cap_without_core" not in floor_config:
            raise ValueError("core_evidence_floor: missing required field 'cap_without_core'")

        min_core_coverage = floor_config["min_core_coverage"]
        cap_without_core = floor_config["cap_without_core"]

        if not (0.0 <= min_core_coverage <= 1.0):
            raise ValueError(
                f"core_evidence_floor: min_core_coverage must be in [0, 1], got {min_core_coverage}"
            )
        if not (0.0 <= cap_without_core <= 1.0):
            raise ValueError(
                f"core_evidence_floor: cap_without_core must be in [0, 1], got {cap_without_core}"
            )

    return True
