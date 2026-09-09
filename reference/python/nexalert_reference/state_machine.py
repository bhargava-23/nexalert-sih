"""
Hazard State Machine reference implementation.

Specification: Document 04, Section 10
Deterministic hazard state tracking with hysteresis and persistence.

States: NORMAL, WATCH, SUSPECTED, CONFIRMED, CRITICAL, RESOLVED
Transitions: Deterministic based on E_h, C_h, S_h, R_h, A_h inputs
Hysteresis: Separate enter/exit thresholds prevent flapping
Persistence: Sample-count requirements distinguish transient from sustained

CRITICAL INVARIANT: UNKNOWN prevents NEW CONFIRMED declarations
UNKNOWN information condition prevents NEW CONFIRMED hazard declarations when
minimum confidence/coverage gates are not satisfied. However, UNKNOWN does not
invalidate an already-established CONFIRMED or CRITICAL hazard; existing hazards
may escalate based on valid severity/risk evidence under the safety-first
escalation rules.

PHASE 5 ITERATION 6: Hazard state machine.

Design Corrections Applied:
- Fast paths bypass persistence/intermediate states ONLY, NOT information gates
- CONFIRMED → CRITICAL allows any info condition (safety-first, existing hazard)
- Fast SUSPECTED → CRITICAL requires minimum DEGRADED (blocks UNKNOWN)
- Baseline freeze is post-transition operational command (temporal separation)
- RESOLVED is autonomous sensor-based determination (NOT human approval)
- Sample-count persistence is deterministic but sample-rate dependent

Provenance: ALL threshold and persistence values are PROTOTYPE ASSUMPTIONS
Validation Status: UNVALIDATED - NOT scientifically authoritative
Owner: Phase 5 implementation (requires domain expert takeover)
Config Version: 1.0-prototype
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Numerical constants
EPSILON = 1e-9


class HazardState(str, Enum):
    """
    Hazard state enumeration.

    Specification: Document 04, Section 10.1
    """
    NORMAL = "NORMAL"          # No meaningful hazard hypothesis
    WATCH = "WATCH"            # Something meaningful changing
    SUSPECTED = "SUSPECTED"    # Hazard plausible but incomplete
    CONFIRMED = "CONFIRMED"    # Evidence supports credible declaration
    CRITICAL = "CRITICAL"      # Urgent/severe/rapidly escalating
    RESOLVED = "RESOLVED"      # Hazard subsided, sustained safe conditions


class InformationCondition(str, Enum):
    """
    Information quality condition.

    Specification: Document 04, Section 10.2
    Independent of hazard state.
    """
    GOOD = "GOOD"              # Sufficient observations available
    DEGRADED = "DEGRADED"      # Important limitations but reasoning possible
    UNKNOWN = "UNKNOWN"        # Cannot responsibly characterize situation


@dataclass
class StateTransition:
    """
    Result of state machine update.

    Fields:
        new_state: Resulting hazard state
        prev_state: Previous hazard state
        reason: Human-readable transition reason
        persistence_counter: Updated persistence counter value
        resolved_hold_start: Timestamp when RESOLVED entered (None if not in RESOLVED)
        should_freeze_baseline: True if baseline should be frozen (post-transition command)
    """
    new_state: HazardState
    prev_state: HazardState
    reason: str
    persistence_counter: int
    resolved_hold_start: Optional[float]
    should_freeze_baseline: bool


# Default configuration (PROTOTYPE, UNVALIDATED)
DEFAULT_STATE_MACHINE_CONFIG = {
    "hazard_type": "fire",

    # Escalation thresholds (enter)
    "thresholds": {
        "watch_risk_enter": 0.3,
        "watch_anomaly_enter": 0.5,
        "suspected_evidence_enter": 0.4,
        "confirmed_evidence_enter": 0.7,
        "confirmed_confidence_min": 0.6,
        "confirmed_core_coverage_min": 0.7,
        "critical_severity_enter": 0.85,
        "critical_risk_enter": 0.9,
        "resolved_evidence_max": 0.2,
        "resolved_risk_max": 0.2,
    },

    # De-escalation thresholds (exit, with hysteresis)
    "hysteresis": {
        "watch_risk_exit": 0.25,
        "suspected_evidence_exit": 0.35,
        "confirmed_evidence_exit": 0.65,
        "confirmed_confidence_min_exit": 0.55,
        "confirmed_core_coverage_min_exit": 0.65,
        "critical_severity_exit": 0.80,
        "critical_risk_exit": 0.85,
    },

    # Persistence requirements (samples)
    "persistence": {
        "watch_enter": 1,
        "suspected_enter": 3,
        "confirmed_enter": 5,
        "critical_enter": 1,
        "resolved_enter": 10,
        "deescalate": 3,
    },

    # Fast escalation
    "fast_paths": {
        "watch_to_confirmed_evidence": 0.85,
        "watch_to_confirmed_severity": 0.8,
        "watch_to_confirmed_confidence": 0.6,  # CORRECTED: enforced
        "watch_to_confirmed_core_coverage": 0.7,  # CORRECTED: enforced
        "watch_to_confirmed_persistence": 2,
        "suspected_to_critical_severity": 0.9,
        "suspected_to_critical_temporal": 0.8,
        "suspected_to_critical_confidence": 0.4,  # CORRECTED: blocks UNKNOWN
        "suspected_to_critical_core_coverage": 0.5,  # CORRECTED: blocks UNKNOWN
    },

    # RESOLVED hold
    "resolved_hold_seconds": 300.0,  # 5 minutes

    # Information condition
    "information_condition": {
        "good_confidence_min": 0.7,
        "good_core_coverage_min": 0.8,
        "degraded_confidence_min": 0.4,
        "degraded_core_coverage_min": 0.5,
    },

    # Staleness
    "max_staleness_seconds": 60.0,

    # Provenance metadata
    "provenance": "PROTOTYPE ASSUMPTIONS",
    "validation_status": "UNVALIDATED",
    "owner": "Phase 5 implementation",
    "config_version": "1.0-prototype"
}


def compute_information_condition(
    confidence: Optional[float],
    core_coverage: Optional[float],
    baseline_status: str,
    config: Dict,
    epsilon: float = EPSILON
) -> InformationCondition:
    """
    Compute information condition from confidence and sensor availability.

    Specification: Document 04, Section 10.2

    Args:
        confidence: C_h confidence assessment [0, 1] or None
        core_coverage: Core sensor coverage [0, 1] or None
        baseline_status: Baseline state (INITIALIZING/LEARNING/READY/FROZEN/RECOVERING)
        config: State machine configuration
        epsilon: Numerical epsilon

    Returns:
        InformationCondition (GOOD, DEGRADED, or UNKNOWN)

    GOOD:
        - C_h ≥ good_confidence_min (default 0.7)
        - core_coverage ≥ good_core_coverage_min (default 0.8)
        - Baseline not INITIALIZING

    DEGRADED:
        - degraded_confidence_min ≤ C_h < good_confidence_min
        - OR degraded_core_coverage_min ≤ core_coverage < good_core_coverage_min
        - Baseline not INITIALIZING

    UNKNOWN:
        - C_h < degraded_confidence_min (default 0.4)
        - OR core_coverage < degraded_core_coverage_min (default 0.5)
        - OR baseline_status = INITIALIZING
    """
    info_config = config.get("information_condition", {})
    good_conf = info_config.get("good_confidence_min", 0.7)
    good_cov = info_config.get("good_core_coverage_min", 0.8)
    deg_conf = info_config.get("degraded_confidence_min", 0.4)
    deg_cov = info_config.get("degraded_core_coverage_min", 0.5)

    # UNKNOWN if baseline INITIALIZING
    if baseline_status == "INITIALIZING":
        return InformationCondition.UNKNOWN

    # UNKNOWN if confidence or coverage too low
    if confidence is not None and confidence < deg_conf - epsilon:
        return InformationCondition.UNKNOWN
    if core_coverage is not None and core_coverage < deg_cov - epsilon:
        return InformationCondition.UNKNOWN

    # GOOD if both confidence and coverage high
    if (confidence is not None and confidence >= good_conf - epsilon and
        core_coverage is not None and core_coverage >= good_cov - epsilon):
        return InformationCondition.GOOD

    # Otherwise DEGRADED (moderate confidence/coverage)
    return InformationCondition.DEGRADED


def update_state(
    current_state: HazardState,
    intelligence: Dict[str, Optional[float]],
    baseline_status: str,
    timestamp: float,
    persistence_counter: int,
    resolved_hold_start: Optional[float],
    config: Dict,
    epsilon: float = EPSILON
) -> StateTransition:
    """
    Update hazard state based on current intelligence outputs.

    Specification: Document 04, Section 10

    Args:
        current_state: Previous hazard state
        intelligence: Current intelligence outputs with keys:
            - E_h: Evidence [0, 1] or None
            - C_h: Confidence [0, 1] or None
            - S_h: Severity [0, 1] or None
            - R_h: Risk [0, 1] or None
            - A_h: Hazard-specific anomaly [0, 1] or None
            - core_coverage: Core sensor coverage [0, 1] or None
        baseline_status: Current baseline state
        timestamp: Current measurement timestamp (seconds)
        persistence_counter: Previous persistence counter value
        resolved_hold_start: Timestamp when RESOLVED entered (None if not in RESOLVED)
        config: State machine configuration
        epsilon: Numerical epsilon for comparisons

    Returns:
        StateTransition with new state, reason, updated counters, freeze command

    Deterministic: Same inputs + config → same output

    State Transition Rules:
        NORMAL → WATCH: R_h ≥ 0.3 OR A_h ≥ 0.5
        WATCH → SUSPECTED: E_h ≥ 0.4
        SUSPECTED → CONFIRMED: E_h ≥ 0.7, C_h ≥ 0.6, core ≥ 0.7
        CONFIRMED → CRITICAL: S_h ≥ 0.85 OR R_h ≥ 0.9
        Any → RESOLVED: E_h < 0.2, R_h < 0.2
        RESOLVED → NORMAL: After 300s hold

    Fast Paths (CORRECTED - information gates enforced):
        WATCH → CONFIRMED: E_h ≥ 0.85, S_h ≥ 0.8, C_h ≥ 0.6, core ≥ 0.7
        SUSPECTED → CRITICAL: S_h ≥ 0.9, T_h ≥ 0.8, C_h ≥ 0.4, core ≥ 0.5

    Critical Invariant:
        UNKNOWN blocks NEW CONFIRMED declarations but does NOT invalidate
        existing CONFIRMED/CRITICAL hazards. Existing hazards may escalate
        under UNKNOWN based on valid severity/risk evidence.
    """
    # Extract intelligence
    E_h = intelligence.get("E_h")
    C_h = intelligence.get("C_h")
    S_h = intelligence.get("S_h")
    R_h = intelligence.get("R_h")
    A_h = intelligence.get("A_h")
    T_h = intelligence.get("T_h")  # For fast SUSPECTED → CRITICAL
    core_coverage = intelligence.get("core_coverage")

    # Extract thresholds
    thresholds = config.get("thresholds", {})
    hysteresis = config.get("hysteresis", {})
    persistence_config = config.get("persistence", {})
    fast_paths = config.get("fast_paths", {})

    # Initialize result
    new_state = current_state
    reason = "No transition"
    new_counter = persistence_counter
    new_resolved_start = resolved_hold_start
    should_freeze = False

    # Evaluate transitions based on current state
    if current_state == HazardState.NORMAL:
        # NORMAL → WATCH
        watch_risk_enter = thresholds.get("watch_risk_enter", 0.3)
        watch_anom_enter = thresholds.get("watch_anomaly_enter", 0.5)

        if ((R_h is not None and R_h >= watch_risk_enter - epsilon) or
            (A_h is not None and A_h >= watch_anom_enter - epsilon)):
            new_counter += 1
            if new_counter >= persistence_config.get("watch_enter", 1):
                new_state = HazardState.WATCH
                reason = f"Risk/anomaly crosses watch threshold (R_h={R_h}, A_h={A_h})"
                new_counter = 0
        else:
            new_counter = 0

    elif current_state == HazardState.WATCH:
        # Check for de-escalation to RESOLVED first
        resolved_e_max = thresholds.get("resolved_evidence_max", 0.2)
        resolved_r_max = thresholds.get("resolved_risk_max", 0.2)

        if ((E_h is not None and E_h < resolved_e_max + epsilon) and
            (R_h is not None and R_h < resolved_r_max + epsilon)):
            new_counter += 1
            if new_counter >= persistence_config.get("resolved_enter", 10):
                new_state = HazardState.RESOLVED
                new_resolved_start = timestamp
                reason = f"Evidence and risk drop below resolution thresholds (E_h={E_h}, R_h={R_h})"
                new_counter = 0
        else:
            # Check for fast path WATCH → CONFIRMED
            fast_e = fast_paths.get("watch_to_confirmed_evidence", 0.85)
            fast_s = fast_paths.get("watch_to_confirmed_severity", 0.8)
            fast_c = fast_paths.get("watch_to_confirmed_confidence", 0.6)  # CORRECTED
            fast_cov = fast_paths.get("watch_to_confirmed_core_coverage", 0.7)  # CORRECTED
            fast_pers = fast_paths.get("watch_to_confirmed_persistence", 2)

            # Fast path: requires information gates (CORRECTED)
            if (E_h is not None and E_h >= fast_e - epsilon and
                S_h is not None and S_h >= fast_s - epsilon and
                C_h is not None and C_h >= fast_c - epsilon and
                core_coverage is not None and core_coverage >= fast_cov - epsilon):
                new_counter += 1
                if new_counter >= fast_pers:
                    new_state = HazardState.CONFIRMED
                    reason = f"Fast escalation: high evidence + severity + confidence (E_h={E_h}, S_h={S_h}, C_h={C_h})"
                    new_counter = 0
                    should_freeze = True
            else:
                # Normal path WATCH → SUSPECTED
                susp_e_enter = thresholds.get("suspected_evidence_enter", 0.4)

                if E_h is not None and E_h >= susp_e_enter - epsilon:
                    new_counter += 1
                    if new_counter >= persistence_config.get("suspected_enter", 3):
                        new_state = HazardState.SUSPECTED
                        reason = f"Evidence crosses suspected threshold (E_h={E_h})"
                        new_counter = 0
                else:
                    new_counter = 0

    elif current_state == HazardState.SUSPECTED:
        # Check for de-escalation to RESOLVED first
        resolved_e_max = thresholds.get("resolved_evidence_max", 0.2)
        resolved_r_max = thresholds.get("resolved_risk_max", 0.2)

        if ((E_h is not None and E_h < resolved_e_max + epsilon) and
            (R_h is not None and R_h < resolved_r_max + epsilon)):
            new_counter += 1
            if new_counter >= persistence_config.get("resolved_enter", 10):
                new_state = HazardState.RESOLVED
                new_resolved_start = timestamp
                reason = f"Evidence and risk drop below resolution thresholds (E_h={E_h}, R_h={R_h})"
                new_counter = 0
        else:
            # Check for fast path SUSPECTED → CRITICAL
            fast_s = fast_paths.get("suspected_to_critical_severity", 0.9)
            fast_t = fast_paths.get("suspected_to_critical_temporal", 0.8)
            fast_c = fast_paths.get("suspected_to_critical_confidence", 0.4)  # CORRECTED
            fast_cov = fast_paths.get("suspected_to_critical_core_coverage", 0.5)  # CORRECTED

            # Fast path: requires minimum DEGRADED (blocks UNKNOWN)
            if (S_h is not None and S_h >= fast_s - epsilon and
                T_h is not None and T_h >= fast_t - epsilon and
                C_h is not None and C_h >= fast_c - epsilon and
                core_coverage is not None and core_coverage >= fast_cov - epsilon):
                new_counter += 1
                if new_counter >= 1:  # Immediate
                    new_state = HazardState.CRITICAL
                    reason = f"Fast escalation: extreme severity + rapid escalation (S_h={S_h}, T_h={T_h})"
                    new_counter = 0
                    should_freeze = True
            else:
                # Check for de-escalation SUSPECTED → WATCH
                susp_e_exit = hysteresis.get("suspected_evidence_exit", 0.35)

                if E_h is not None and E_h < susp_e_exit + epsilon:
                    new_counter += 1
                    if new_counter >= persistence_config.get("deescalate", 3):
                        new_state = HazardState.WATCH
                        reason = f"Evidence drops below suspected exit threshold (E_h={E_h})"
                        new_counter = 0
                else:
                    # Normal path SUSPECTED → CONFIRMED
                    conf_e_enter = thresholds.get("confirmed_evidence_enter", 0.7)
                    conf_c_min = thresholds.get("confirmed_confidence_min", 0.6)
                    conf_cov_min = thresholds.get("confirmed_core_coverage_min", 0.7)

                    # CRITICAL: Information gates enforced (blocks UNKNOWN)
                    if (E_h is not None and E_h >= conf_e_enter - epsilon and
                        C_h is not None and C_h >= conf_c_min - epsilon and
                        core_coverage is not None and core_coverage >= conf_cov_min - epsilon):
                        new_counter += 1
                        if new_counter >= persistence_config.get("confirmed_enter", 5):
                            new_state = HazardState.CONFIRMED
                            reason = f"High evidence + confidence + coverage (E_h={E_h}, C_h={C_h}, core={core_coverage})"
                            new_counter = 0
                            should_freeze = True
                    else:
                        new_counter = 0

    elif current_state == HazardState.CONFIRMED:
        # Check for de-escalation to RESOLVED first
        resolved_e_max = thresholds.get("resolved_evidence_max", 0.2)
        resolved_r_max = thresholds.get("resolved_risk_max", 0.2)

        if ((E_h is not None and E_h < resolved_e_max + epsilon) and
            (R_h is not None and R_h < resolved_r_max + epsilon)):
            new_counter += 1
            if new_counter >= persistence_config.get("resolved_enter", 10):
                new_state = HazardState.RESOLVED
                new_resolved_start = timestamp
                reason = f"Evidence and risk drop below resolution thresholds (E_h={E_h}, R_h={R_h})"
                new_counter = 0
                should_freeze = False  # Unfreeze on RESOLVED
        else:
            # Check for escalation CONFIRMED → CRITICAL
            crit_s_enter = thresholds.get("critical_severity_enter", 0.85)
            crit_r_enter = thresholds.get("critical_risk_enter", 0.9)

            # CORRECTED: No information gate (existing hazard, safety-first)
            # UNKNOWN allowed (does not invalidate established hazard)
            if ((S_h is not None and S_h >= crit_s_enter - epsilon) or
                (R_h is not None and R_h >= crit_r_enter - epsilon)):
                new_counter += 1
                if new_counter >= persistence_config.get("critical_enter", 1):
                    new_state = HazardState.CRITICAL
                    reason = f"Extreme severity or risk (S_h={S_h}, R_h={R_h})"
                    new_counter = 0
                    # Already frozen, stay frozen
            else:
                # Check for de-escalation CONFIRMED → SUSPECTED
                conf_e_exit = hysteresis.get("confirmed_evidence_exit", 0.65)
                conf_c_exit = hysteresis.get("confirmed_confidence_min_exit", 0.55)
                conf_cov_exit = hysteresis.get("confirmed_core_coverage_min_exit", 0.65)

                if ((E_h is not None and E_h < conf_e_exit + epsilon) or
                    (C_h is not None and C_h < conf_c_exit + epsilon) or
                    (core_coverage is not None and core_coverage < conf_cov_exit + epsilon)):
                    new_counter += 1
                    if new_counter >= persistence_config.get("deescalate", 5):
                        new_state = HazardState.SUSPECTED
                        reason = f"Evidence/confidence/coverage drops (E_h={E_h}, C_h={C_h}, core={core_coverage})"
                        new_counter = 0
                        should_freeze = False  # Unfreeze on de-escalation
                else:
                    new_counter = 0

    elif current_state == HazardState.CRITICAL:
        # Check for de-escalation to RESOLVED first
        resolved_e_max = thresholds.get("resolved_evidence_max", 0.2)
        resolved_r_max = thresholds.get("resolved_risk_max", 0.2)

        if ((E_h is not None and E_h < resolved_e_max + epsilon) and
            (R_h is not None and R_h < resolved_r_max + epsilon)):
            new_counter += 1
            if new_counter >= persistence_config.get("resolved_enter", 10):
                new_state = HazardState.RESOLVED
                new_resolved_start = timestamp
                reason = f"Evidence and risk drop below resolution thresholds (E_h={E_h}, R_h={R_h})"
                new_counter = 0
                should_freeze = False  # Unfreeze on RESOLVED
        else:
            # Check for de-escalation CRITICAL → CONFIRMED
            crit_s_exit = hysteresis.get("critical_severity_exit", 0.80)
            crit_r_exit = hysteresis.get("critical_risk_exit", 0.85)

            if ((S_h is not None and S_h < crit_s_exit + epsilon) and
                (R_h is not None and R_h < crit_r_exit + epsilon)):
                new_counter += 1
                if new_counter >= persistence_config.get("deescalate", 3):
                    new_state = HazardState.CONFIRMED
                    reason = f"Severity and risk drop below critical exit (S_h={S_h}, R_h={R_h})"
                    new_counter = 0
                    # Stay frozen (still CONFIRMED)
            else:
                new_counter = 0

    elif current_state == HazardState.RESOLVED:
        # Check for hold period completion
        resolved_hold = config.get("resolved_hold_seconds", 300.0)

        if resolved_hold_start is not None and (timestamp - resolved_hold_start) >= resolved_hold - epsilon:
            # Check if all metrics remain below watch thresholds
            watch_risk_enter = thresholds.get("watch_risk_enter", 0.3)
            watch_anom_enter = thresholds.get("watch_anomaly_enter", 0.5)

            if ((R_h is None or R_h < watch_risk_enter - epsilon) and
                (A_h is None or A_h < watch_anom_enter - epsilon)):
                new_state = HazardState.NORMAL
                new_resolved_start = None
                reason = f"Hold period complete, all metrics below watch thresholds"
                new_counter = 0
            else:
                # Re-escalation during hold: return to NORMAL first, then re-enter
                new_state = HazardState.NORMAL
                new_resolved_start = None
                reason = f"Re-escalation during hold period (R_h={R_h}, A_h={A_h})"
                new_counter = 0
        else:
            # Still in hold period
            new_counter = 0

    # Determine baseline freeze command (post-transition)
    if new_state in [HazardState.CONFIRMED, HazardState.CRITICAL]:
        should_freeze = True
    elif new_state in [HazardState.RESOLVED, HazardState.NORMAL, HazardState.WATCH, HazardState.SUSPECTED]:
        should_freeze = False

    return StateTransition(
        new_state=new_state,
        prev_state=current_state,
        reason=reason,
        persistence_counter=new_counter,
        resolved_hold_start=new_resolved_start,
        should_freeze_baseline=should_freeze
    )


def should_freeze_baseline(state: HazardState) -> bool:
    """
    Determine if baseline should be frozen for given hazard state.

    Args:
        state: Current hazard state

    Returns:
        True if baseline should be frozen

    Baseline Freeze Rules:
        - CONFIRMED: Freeze (prevent corruption)
        - CRITICAL: Freeze (prevent corruption)
        - RESOLVED/NORMAL/WATCH/SUSPECTED: Unfreeze (allow adaptation)
    """
    return state in [HazardState.CONFIRMED, HazardState.CRITICAL]


def validate_config(config: Dict, epsilon: float = EPSILON) -> Tuple[bool, str]:
    """
    Validate state machine configuration.

    Args:
        config: State machine configuration
        epsilon: Numerical epsilon

    Returns:
        (is_valid, error_message)

    Checks:
        - Hysteresis: enter > exit for all thresholds
        - Persistence: all values ≥ 1
        - Thresholds in [0, 1]
        - Information condition ordering: good > degraded
        - Resolved hold > 0
    """
    thresholds = config.get("thresholds", {})
    hysteresis = config.get("hysteresis", {})
    persistence = config.get("persistence", {})
    info_cond = config.get("information_condition", {})

    # Check hysteresis gaps
    hysteresis_pairs = [
        ("watch_risk_enter", "watch_risk_exit"),
        ("suspected_evidence_enter", "suspected_evidence_exit"),
        ("confirmed_evidence_enter", "confirmed_evidence_exit"),
        ("critical_severity_enter", "critical_severity_exit"),
        ("critical_risk_enter", "critical_risk_exit"),
    ]

    for enter_key, exit_key in hysteresis_pairs:
        enter_val = thresholds.get(enter_key.replace("_enter", "_enter"))
        exit_val = hysteresis.get(exit_key)

        if enter_val is not None and exit_val is not None:
            if enter_val <= exit_val + epsilon:
                return False, f"Hysteresis violation: {enter_key} ({enter_val}) must be > {exit_key} ({exit_val})"

    # Check persistence values
    for key, val in persistence.items():
        if val < 1:
            return False, f"Persistence {key} must be >= 1, got {val}"

    # Check threshold ranges
    for key, val in thresholds.items():
        if val < 0 or val > 1:
            return False, f"Threshold {key} must be in [0, 1], got {val}"

    # Check information condition ordering
    good_conf = info_cond.get("good_confidence_min", 0.7)
    deg_conf = info_cond.get("degraded_confidence_min", 0.4)

    if good_conf <= deg_conf + epsilon:
        return False, f"Information condition: good_confidence_min ({good_conf}) must be > degraded_confidence_min ({deg_conf})"

    # Check resolved hold
    resolved_hold = config.get("resolved_hold_seconds", 300.0)
    if resolved_hold <= 0:
        return False, f"resolved_hold_seconds must be > 0, got {resolved_hold}"

    return True, "Configuration valid"


def format_transition_reason(
    prev_state: HazardState,
    new_state: HazardState,
    intelligence: Dict[str, Optional[float]],
    fast_path: bool = False
) -> str:
    """
    Format human-readable transition reason for logging.

    Args:
        prev_state: Previous hazard state
        new_state: New hazard state
        intelligence: Current intelligence values
        fast_path: Whether transition used fast path

    Returns:
        Human-readable transition reason string
    """
    if prev_state == new_state:
        return "No transition"

    E_h = intelligence.get("E_h")
    C_h = intelligence.get("C_h")
    S_h = intelligence.get("S_h")
    R_h = intelligence.get("R_h")
    A_h = intelligence.get("A_h")
    core_cov = intelligence.get("core_coverage")

    transition = f"{prev_state} → {new_state}"

    if fast_path:
        if prev_state == HazardState.WATCH and new_state == HazardState.CONFIRMED:
            return f"{transition} (fast path: E_h={E_h}, S_h={S_h}, C_h={C_h})"
        elif prev_state == HazardState.SUSPECTED and new_state == HazardState.CRITICAL:
            return f"{transition} (fast path: S_h={S_h}, T_h={intelligence.get('T_h')})"

    if new_state == HazardState.WATCH:
        return f"{transition}: Risk/anomaly crosses watch threshold (R_h={R_h}, A_h={A_h})"
    elif new_state == HazardState.SUSPECTED:
        return f"{transition}: Evidence crosses suspected threshold (E_h={E_h})"
    elif new_state == HazardState.CONFIRMED:
        return f"{transition}: High evidence + confidence + coverage (E_h={E_h}, C_h={C_h}, core={core_cov})"
    elif new_state == HazardState.CRITICAL:
        return f"{transition}: Extreme severity or risk (S_h={S_h}, R_h={R_h})"
    elif new_state == HazardState.RESOLVED:
        return f"{transition}: Evidence and risk below resolution thresholds (E_h={E_h}, R_h={R_h})"
    elif new_state == HazardState.NORMAL:
        return f"{transition}: Hold period complete or re-escalation handled"

    return transition
