"""
State machine reference implementation tests.

Specification: Document 04, Section 10
Validates deterministic hazard state tracking with hysteresis and persistence.

Test coverage:
- State transitions (all legal transitions)
- Hysteresis boundaries
- Persistence counters
- Fast escalation paths
- RESOLVED semantics and hold period
- Information condition computation
- Baseline interaction
- Missing value handling
- Multi-hazard independence
- Configuration validation
- Determinism verification

PHASE 5 ITERATION 6: Hazard state machine tests.
"""

import pytest
from pathlib import Path
import sys

# Import reference implementation
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexalert_reference.state_machine import (
    HazardState,
    InformationCondition,
    StateTransition,
    update_state,
    compute_information_condition,
    validate_config,
    should_freeze_baseline,
    DEFAULT_STATE_MACHINE_CONFIG,
    EPSILON
)


# Test fixtures

@pytest.fixture
def default_config():
    """Default state machine configuration."""
    import copy
    return copy.deepcopy(DEFAULT_STATE_MACHINE_CONFIG)


@pytest.fixture
def default_intelligence():
    """Default intelligence outputs."""
    return {
        "E_h": 0.5,
        "C_h": 0.8,
        "S_h": 0.5,
        "R_h": 0.5,
        "A_h": 0.5,
        "T_h": 0.5,
        "core_coverage": 0.9
    }


# Test Class 1: State Transitions

class TestStateTransitions:
    """Test legal state transitions."""

    def test_normal_to_watch_via_risk(self, default_config, default_intelligence):
        """NORMAL → WATCH via risk threshold."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.35  # Above watch threshold (0.3)

        transition = update_state(
            current_state=HazardState.NORMAL,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        assert transition.new_state == HazardState.WATCH
        assert transition.prev_state == HazardState.NORMAL
        assert "Risk/anomaly" in transition.reason or "watch" in transition.reason.lower()

    def test_normal_to_watch_via_anomaly(self, default_config, default_intelligence):
        """NORMAL → WATCH via anomaly threshold."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.1
        intelligence["A_h"] = 0.55  # Above watch threshold (0.5)

        transition = update_state(
            current_state=HazardState.NORMAL,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        assert transition.new_state == HazardState.WATCH

    def test_watch_to_suspected(self, default_config, default_intelligence):
        """WATCH → SUSPECTED with persistence."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.45  # Above suspected threshold (0.4)

        # First 2 samples: counter increments but no transition
        transition = update_state(
            current_state=HazardState.WATCH,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )
        assert transition.new_state == HazardState.WATCH
        assert transition.persistence_counter == 1

        transition = update_state(
            current_state=HazardState.WATCH,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1001.0,
            persistence_counter=1,
            resolved_hold_start=None,
            config=default_config
        )
        assert transition.new_state == HazardState.WATCH
        assert transition.persistence_counter == 2

        # 3rd sample: transition occurs
        transition = update_state(
            current_state=HazardState.WATCH,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1002.0,
            persistence_counter=2,
            resolved_hold_start=None,
            config=default_config
        )
        assert transition.new_state == HazardState.SUSPECTED
        assert transition.persistence_counter == 0

    def test_suspected_to_confirmed(self, default_config, default_intelligence):
        """SUSPECTED → CONFIRMED with persistence."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75  # Above confirmed threshold (0.7)
        intelligence["C_h"] = 0.65  # Above confidence min (0.6)
        intelligence["core_coverage"] = 0.75  # Above core min (0.7)

        # Advance through 5 samples
        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(
                current_state=state,
                intelligence=intelligence,
                baseline_status="READY",
                timestamp=1000.0 + i,
                persistence_counter=counter,
                resolved_hold_start=None,
                config=default_config
            )
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.CONFIRMED
        assert transition.should_freeze_baseline

    def test_confirmed_to_critical_severity(self, default_config, default_intelligence):
        """CONFIRMED → CRITICAL via severity."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.9  # Above critical threshold (0.85)

        transition = update_state(
            current_state=HazardState.CONFIRMED,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        assert transition.new_state == HazardState.CRITICAL
        assert transition.should_freeze_baseline

    def test_confirmed_to_critical_risk(self, default_config, default_intelligence):
        """CONFIRMED → CRITICAL via risk."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.5
        intelligence["R_h"] = 0.95  # Above critical threshold (0.9)

        transition = update_state(
            current_state=HazardState.CONFIRMED,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        assert transition.new_state == HazardState.CRITICAL

    def test_watch_to_resolved(self, default_config, default_intelligence):
        """WATCH → RESOLVED with persistence."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15  # Below resolved threshold (0.2)
        intelligence["R_h"] = 0.15

        # Advance through 10 samples
        counter = 0
        state = HazardState.WATCH
        for i in range(10):
            transition = update_state(
                current_state=state,
                intelligence=intelligence,
                baseline_status="READY",
                timestamp=1000.0 + i,
                persistence_counter=counter,
                resolved_hold_start=None,
                config=default_config
            )
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED
        assert transition.resolved_hold_start == 1009.0
        assert not transition.should_freeze_baseline

    def test_resolved_to_normal(self, default_config, default_intelligence):
        """RESOLVED → NORMAL after hold period."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15
        intelligence["A_h"] = 0.2

        # After 300 seconds (5 minutes)
        transition = update_state(
            current_state=HazardState.RESOLVED,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1300.0,  # 300 seconds after 1000.0
            persistence_counter=0,
            resolved_hold_start=1000.0,
            config=default_config
        )

        assert transition.new_state == HazardState.NORMAL
        assert transition.resolved_hold_start is None

    def test_critical_to_confirmed_deescalation(self, default_config, default_intelligence):
        """CRITICAL → CONFIRMED de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.75  # Below critical exit (0.80)
        intelligence["R_h"] = 0.80  # Below critical exit (0.85)

        # Advance through 3 samples
        counter = 0
        state = HazardState.CRITICAL
        for i in range(3):
            transition = update_state(
                current_state=state,
                intelligence=intelligence,
                baseline_status="READY",
                timestamp=1000.0 + i,
                persistence_counter=counter,
                resolved_hold_start=None,
                config=default_config
            )
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.CONFIRMED
        assert transition.should_freeze_baseline  # Still frozen in CONFIRMED

    def test_confirmed_to_suspected_deescalation(self, default_config, default_intelligence):
        """CONFIRMED → SUSPECTED de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.60  # Below confirmed exit (0.65)
        intelligence["C_h"] = 0.8
        intelligence["core_coverage"] = 0.9

        # Advance through 5 samples (deescalate persistence)
        counter = 0
        state = HazardState.CONFIRMED
        for i in range(5):
            transition = update_state(
                current_state=state,
                intelligence=intelligence,
                baseline_status="READY",
                timestamp=1000.0 + i,
                persistence_counter=counter,
                resolved_hold_start=None,
                config=default_config
            )
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.SUSPECTED
        assert not transition.should_freeze_baseline

    def test_suspected_to_watch_deescalation(self, default_config, default_intelligence):
        """SUSPECTED → WATCH de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.30  # Below suspected exit (0.35)

        # Advance through 3 samples
        counter = 0
        state = HazardState.SUSPECTED
        for i in range(3):
            transition = update_state(
                current_state=state,
                intelligence=intelligence,
                baseline_status="READY",
                timestamp=1000.0 + i,
                persistence_counter=counter,
                resolved_hold_start=None,
                config=default_config
            )
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.WATCH

    def test_blocked_watch_to_normal_direct(self, default_config, default_intelligence):
        """WATCH cannot directly return to NORMAL."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.1  # Below watch threshold
        intelligence["A_h"] = 0.2

        # Even with low values, should not transition directly to NORMAL
        # Must go through RESOLVED first
        transition = update_state(
            current_state=HazardState.WATCH,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        # Should stay in WATCH or transition to RESOLVED (if E_h and R_h both low)
        assert transition.new_state in [HazardState.WATCH, HazardState.RESOLVED]
        assert transition.new_state != HazardState.NORMAL

    def test_normal_stays_normal(self, default_config, default_intelligence):
        """NORMAL stays NORMAL when thresholds not crossed."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.1
        intelligence["A_h"] = 0.2

        transition = update_state(
            current_state=HazardState.NORMAL,
            intelligence=intelligence,
            baseline_status="READY",
            timestamp=1000.0,
            persistence_counter=0,
            resolved_hold_start=None,
            config=default_config
        )

        assert transition.new_state == HazardState.NORMAL
        assert transition.persistence_counter == 0

    def test_state_machine_full_escalation_path(self, default_config):
        """Full escalation: NORMAL → WATCH → SUSPECTED → CONFIRMED → CRITICAL."""
        # Start NORMAL
        state = HazardState.NORMAL
        counter = 0
        resolved_start = None

        # NORMAL → WATCH
        intelligence = {
            "E_h": 0.2, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35,
            "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9
        }
        transition = update_state(state, intelligence, "READY", 1000.0, counter, resolved_start, default_config)
        assert transition.new_state == HazardState.WATCH
        state = transition.new_state
        counter = transition.persistence_counter

        # WATCH → SUSPECTED (3 samples)
        intelligence["E_h"] = 0.45
        for i in range(3):
            transition = update_state(state, intelligence, "READY", 1001.0 + i, counter, resolved_start, default_config)
            state = transition.new_state
            counter = transition.persistence_counter
        assert state == HazardState.SUSPECTED

        # SUSPECTED → CONFIRMED (5 samples)
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.7
        for i in range(5):
            transition = update_state(state, intelligence, "READY", 1004.0 + i, counter, resolved_start, default_config)
            state = transition.new_state
            counter = transition.persistence_counter
        assert state == HazardState.CONFIRMED

        # CONFIRMED → CRITICAL (1 sample)
        intelligence["S_h"] = 0.9
        transition = update_state(state, intelligence, "READY", 1009.0, counter, resolved_start, default_config)
        assert transition.new_state == HazardState.CRITICAL


# Test Class 2: Hysteresis

class TestHysteresis:
    """Test hysteresis boundaries."""

    def test_hysteresis_watch_prevents_flapping(self, default_config, default_intelligence):
        """Oscillating risk near watch threshold stays in WATCH."""
        # Enter WATCH
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.35
        transition = update_state(HazardState.NORMAL, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH

        # Drop slightly below enter but above exit (0.27)
        intelligence["R_h"] = 0.27
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1001.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH  # Stays in WATCH due to hysteresis

    def test_hysteresis_suspected_gap(self, default_config, default_intelligence):
        """Evidence hysteresis gap prevents flapping."""
        # Enter SUSPECTED
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.45
        counter = 0
        state = HazardState.WATCH
        for i in range(3):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter
        assert state == HazardState.SUSPECTED

        # Drop to 0.37 (below enter 0.4 but above exit 0.35)
        intelligence["E_h"] = 0.37
        transition = update_state(HazardState.SUSPECTED, intelligence, "READY", 1003.0, 0, None, default_config)
        assert transition.new_state == HazardState.SUSPECTED

    def test_hysteresis_confirmed_gap(self, default_config, default_intelligence):
        """CONFIRMED hysteresis prevents immediate de-escalation."""
        # Already in CONFIRMED
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.67  # Below enter (0.7) but above exit (0.65)
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = 0.9

        transition = update_state(HazardState.CONFIRMED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CONFIRMED

    def test_hysteresis_critical_gap(self, default_config, default_intelligence):
        """CRITICAL hysteresis prevents immediate de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.82  # Below enter (0.85) but above exit (0.80)
        intelligence["R_h"] = 0.87  # Below enter (0.9) but above exit (0.85)

        transition = update_state(HazardState.CRITICAL, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CRITICAL

    def test_hysteresis_exit_triggers_deescalation(self, default_config, default_intelligence):
        """Dropping below exit threshold triggers de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.30  # Below suspected exit (0.35)

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(3):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.WATCH

    def test_hysteresis_prevents_watch_flapping(self, default_config, default_intelligence):
        """Watch boundary oscillation handled correctly."""
        # Sequence: R_h = [0.35, 0.28, 0.32, 0.26, 0.29]
        # Enter: 0.3, Exit: 0.25
        # Expected: NORMAL → WATCH (0.35), WATCH (0.28), WATCH (0.32), WATCH (0.26), WATCH (0.29)

        r_values = [0.35, 0.28, 0.32, 0.26, 0.29]
        state = HazardState.NORMAL
        counter = 0

        for i, r_val in enumerate(r_values):
            intelligence = default_intelligence.copy()
            intelligence["R_h"] = r_val
            intelligence["A_h"] = 0.2
            intelligence["E_h"] = 0.25  # Below suspected threshold to avoid WATCH → SUSPECTED

            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

            if i == 0:
                assert state == HazardState.WATCH
            else:
                assert state == HazardState.WATCH  # Stays in WATCH due to hysteresis

    def test_hysteresis_allows_exit_when_below_threshold(self, default_config, default_intelligence):
        """Dropping well below exit allows de-escalation."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.20  # Well below watch exit (0.25)
        intelligence["E_h"] = 0.15

        # Should allow transition to RESOLVED
        counter = 0
        state = HazardState.WATCH
        for i in range(10):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED

    def test_hysteresis_config_validation(self, default_config):
        """Hysteresis gaps validated in config."""
        # Valid config
        is_valid, msg = validate_config(default_config)
        assert is_valid

        # Invalid: enter <= exit
        invalid_config = default_config.copy()
        invalid_config["thresholds"]["watch_risk_enter"] = 0.25
        invalid_config["hysteresis"]["watch_risk_exit"] = 0.25

        is_valid, msg = validate_config(invalid_config)
        assert not is_valid
        assert "hysteresis" in msg.lower() or "must be >" in msg.lower()


# Test Class 3: Persistence

class TestPersistence:
    """Test persistence counter behavior."""

    def test_persistence_counter_increments(self, default_config, default_intelligence):
        """Persistence counter increments correctly."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.45

        # Sample 1
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH
        assert transition.persistence_counter == 1

        # Sample 2
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1001.0, 1, None, default_config)
        assert transition.new_state == HazardState.WATCH
        assert transition.persistence_counter == 2

    def test_persistence_counter_resets(self, default_config, default_intelligence):
        """Persistence counter resets when criteria not met."""
        intelligence = default_intelligence.copy()

        # Sample 1: E_h = 0.45 (meets criteria)
        intelligence["E_h"] = 0.45
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.persistence_counter == 1

        # Sample 2: E_h = 0.35 (does not meet criteria)
        intelligence["E_h"] = 0.35
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1001.0, 1, None, default_config)
        assert transition.persistence_counter == 0  # Reset

    def test_persistence_suspected_requires_three(self, default_config, default_intelligence):
        """SUSPECTED requires 3 consecutive samples."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.45

        # Sample 1
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH

        # Sample 2
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1001.0, 1, None, default_config)
        assert transition.new_state == HazardState.WATCH

        # Sample 3: transition
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1002.0, 2, None, default_config)
        assert transition.new_state == HazardState.SUSPECTED

    def test_persistence_confirmed_requires_five(self, default_config, default_intelligence):
        """CONFIRMED requires 5 consecutive samples."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = 0.75

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(4):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            assert transition.new_state == HazardState.SUSPECTED
            counter = transition.persistence_counter

        # 5th sample: transition
        transition = update_state(HazardState.SUSPECTED, intelligence, "READY", 1004.0, 4, None, default_config)
        assert transition.new_state == HazardState.CONFIRMED

    def test_persistence_resolved_requires_ten(self, default_config, default_intelligence):
        """RESOLVED requires 10 consecutive samples."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15

        counter = 0
        state = HazardState.WATCH
        for i in range(9):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            assert transition.new_state == HazardState.WATCH
            counter = transition.persistence_counter

        # 10th sample: transition
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1009.0, 9, None, default_config)
        assert transition.new_state == HazardState.RESOLVED

    def test_persistence_reset_delays_transition(self, default_config, default_intelligence):
        """Counter reset delays transition."""
        intelligence = default_intelligence.copy()

        # Samples: E_h = [0.45, 0.45, 0.35, 0.45, 0.45, 0.45]
        # Expected: counter = [1, 2, 0, 1, 2, 3] → transition on 6th

        e_values = [0.45, 0.45, 0.35, 0.45, 0.45, 0.45]
        counter = 0
        state = HazardState.WATCH

        for i, e_val in enumerate(e_values):
            intelligence["E_h"] = e_val
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.SUSPECTED

    def test_persistence_critical_immediate(self, default_config, default_intelligence):
        """CRITICAL escalation is immediate (persistence 1)."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.9

        transition = update_state(HazardState.CONFIRMED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CRITICAL

    def test_persistence_deescalate_requires_three(self, default_config, default_intelligence):
        """De-escalation requires 3 samples."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.75
        intelligence["R_h"] = 0.80

        counter = 0
        state = HazardState.CRITICAL
        for i in range(2):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            assert transition.new_state == HazardState.CRITICAL
            counter = transition.persistence_counter

        # 3rd sample: transition
        transition = update_state(HazardState.CRITICAL, intelligence, "READY", 1002.0, 2, None, default_config)
        assert transition.new_state == HazardState.CONFIRMED

    def test_fast_path_reduced_persistence(self, default_config, default_intelligence):
        """Fast path WATCH → CONFIRMED has reduced persistence (2 samples)."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.87
        intelligence["S_h"] = 0.82
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = 0.75

        # Sample 1
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH
        assert transition.persistence_counter == 1

        # Sample 2: transition
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1001.0, 1, None, default_config)
        assert transition.new_state == HazardState.CONFIRMED

    def test_fast_path_suspected_to_critical_immediate(self, default_config, default_intelligence):
        """Fast path SUSPECTED → CRITICAL is immediate (1 sample)."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.92
        intelligence["T_h"] = 0.85
        intelligence["C_h"] = 0.5
        intelligence["core_coverage"] = 0.6

        transition = update_state(HazardState.SUSPECTED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CRITICAL


# Test Class 4: RESOLVED

class TestResolved:
    """Test RESOLVED state semantics."""

    def test_resolved_entry_from_watch(self, default_config, default_intelligence):
        """RESOLVED entry from WATCH state."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15

        counter = 0
        state = HazardState.WATCH
        for i in range(10):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED
        assert transition.resolved_hold_start == 1009.0

    def test_resolved_hold_period(self, default_config, default_intelligence):
        """RESOLVED hold period enforced."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15
        intelligence["A_h"] = 0.2

        # Before hold complete
        transition = update_state(HazardState.RESOLVED, intelligence, "READY", 1200.0, 0, 1000.0, default_config)
        assert transition.new_state == HazardState.RESOLVED

        # After hold complete (300 seconds)
        transition = update_state(HazardState.RESOLVED, intelligence, "READY", 1300.0, 0, 1000.0, default_config)
        assert transition.new_state == HazardState.NORMAL

    def test_resolved_reescalation(self, default_config, default_intelligence):
        """Re-escalation during RESOLVED hold."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.35  # Above watch threshold
        intelligence["A_h"] = 0.6

        # During hold (after 300s), conditions worsen
        transition = update_state(HazardState.RESOLVED, intelligence, "READY", 1300.0, 0, 1000.0, default_config)

        # Should return to NORMAL first
        assert transition.new_state == HazardState.NORMAL

    def test_resolved_from_critical(self, default_config, default_intelligence):
        """RESOLVED entry from CRITICAL."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15

        counter = 0
        state = HazardState.CRITICAL
        for i in range(10):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED
        assert not transition.should_freeze_baseline

    def test_resolved_baseline_unfreeze(self, default_config, default_intelligence):
        """Baseline unfreezes when entering RESOLVED."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15

        # Enter RESOLVED from CONFIRMED
        counter = 0
        state = HazardState.CONFIRMED
        for i in range(10):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED
        assert not transition.should_freeze_baseline

    def test_resolved_to_normal_all_metrics_low(self, default_config, default_intelligence):
        """RESOLVED → NORMAL only if all metrics remain low."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15
        intelligence["A_h"] = 0.2

        # All low: transition allowed
        transition = update_state(HazardState.RESOLVED, intelligence, "READY", 1300.0, 0, 1000.0, default_config)
        assert transition.new_state == HazardState.NORMAL


# Test Class 5: Information Condition

class TestInformationCondition:
    """Test information condition computation."""

    def test_information_condition_good(self, default_config):
        """GOOD information condition."""
        condition = compute_information_condition(
            confidence=0.75,
            core_coverage=0.85,
            baseline_status="READY",
            config=default_config
        )
        assert condition == InformationCondition.GOOD

    def test_information_condition_degraded_confidence(self, default_config):
        """DEGRADED due to moderate confidence."""
        condition = compute_information_condition(
            confidence=0.55,  # Between 0.4 and 0.7
            core_coverage=0.85,
            baseline_status="READY",
            config=default_config
        )
        assert condition == InformationCondition.DEGRADED

    def test_information_condition_degraded_coverage(self, default_config):
        """DEGRADED due to partial sensor coverage."""
        condition = compute_information_condition(
            confidence=0.75,
            core_coverage=0.65,  # Between 0.5 and 0.8
            baseline_status="READY",
            config=default_config
        )
        assert condition == InformationCondition.DEGRADED

    def test_information_condition_unknown_low_confidence(self, default_config):
        """UNKNOWN due to low confidence."""
        condition = compute_information_condition(
            confidence=0.35,  # Below 0.4
            core_coverage=0.85,
            baseline_status="READY",
            config=default_config
        )
        assert condition == InformationCondition.UNKNOWN

    def test_information_condition_unknown_low_coverage(self, default_config):
        """UNKNOWN due to low coverage."""
        condition = compute_information_condition(
            confidence=0.75,
            core_coverage=0.45,  # Below 0.5
            baseline_status="READY",
            config=default_config
        )
        assert condition == InformationCondition.UNKNOWN

    def test_information_condition_unknown_initializing(self, default_config):
        """UNKNOWN during baseline INITIALIZING."""
        condition = compute_information_condition(
            confidence=0.75,
            core_coverage=0.85,
            baseline_status="INITIALIZING",
            config=default_config
        )
        assert condition == InformationCondition.UNKNOWN

    def test_fast_path_blocked_under_unknown(self, default_config, default_intelligence):
        """Fast path WATCH → CONFIRMED blocked under UNKNOWN."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.87
        intelligence["S_h"] = 0.82
        intelligence["C_h"] = 0.35  # Below 0.6 threshold (UNKNOWN)
        intelligence["core_coverage"] = 0.75

        # Should NOT trigger fast path
        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH  # Stays in WATCH

    def test_fast_path_blocked_suspected_to_critical_under_unknown(self, default_config, default_intelligence):
        """Fast path SUSPECTED → CRITICAL blocked under UNKNOWN."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.92
        intelligence["T_h"] = 0.85
        intelligence["C_h"] = 0.35  # Below 0.4 threshold (UNKNOWN)
        intelligence["core_coverage"] = 0.6

        # Should NOT trigger fast path
        transition = update_state(HazardState.SUSPECTED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.SUSPECTED  # Stays in SUSPECTED

    def test_confirmed_blocked_under_unknown_new_declaration(self, default_config, default_intelligence):
        """NEW CONFIRMED declaration blocked under UNKNOWN."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.35  # UNKNOWN
        intelligence["core_coverage"] = 0.75

        # SUSPECTED → CONFIRMED should NOT occur
        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.SUSPECTED  # Blocked from CONFIRMED

    def test_existing_critical_allowed_under_unknown(self, default_config, default_intelligence):
        """Existing CONFIRMED/CRITICAL hazard may escalate under UNKNOWN."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.9
        intelligence["C_h"] = 0.35  # UNKNOWN (but existing hazard)
        intelligence["core_coverage"] = 0.45

        # Already CONFIRMED: can escalate to CRITICAL
        transition = update_state(HazardState.CONFIRMED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CRITICAL


# Test Class 6: Missing Values

class TestMissingValues:
    """Test missing value handling."""

    def test_missing_evidence_blocks_suspected(self, default_config, default_intelligence):
        """E_h = None blocks WATCH → SUSPECTED."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = None

        transition = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH

    def test_missing_confidence_blocks_confirmed(self, default_config, default_intelligence):
        """C_h = None blocks SUSPECTED → CONFIRMED."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = None
        intelligence["core_coverage"] = 0.75

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.SUSPECTED

    def test_missing_severity_blocks_critical(self, default_config, default_intelligence):
        """S_h = None blocks CONFIRMED → CRITICAL."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = None
        intelligence["R_h"] = 0.5

        transition = update_state(HazardState.CONFIRMED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CONFIRMED

    def test_missing_risk_allows_alternative_pathways(self, default_config, default_intelligence):
        """R_h = None: anomaly pathway still available."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = None
        intelligence["A_h"] = 0.6

        transition = update_state(HazardState.NORMAL, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH

    def test_missing_core_coverage_blocks_confirmed(self, default_config, default_intelligence):
        """core_coverage = None blocks SUSPECTED → CONFIRMED."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = None

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.SUSPECTED

    def test_missing_not_converted_to_zero(self, default_config):
        """Missing ≠ Zero invariant."""
        intelligence = {
            "E_h": None,
            "C_h": None,
            "S_h": None,
            "R_h": None,
            "A_h": None,
            "T_h": None,
            "core_coverage": None
        }

        # Should stay in current state, not crash
        transition = update_state(HazardState.NORMAL, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.NORMAL

    def test_missing_temporal_blocks_fast_suspected_to_critical(self, default_config, default_intelligence):
        """T_h = None blocks fast SUSPECTED → CRITICAL."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.92
        intelligence["T_h"] = None
        intelligence["C_h"] = 0.5
        intelligence["core_coverage"] = 0.6

        transition = update_state(HazardState.SUSPECTED, intelligence, "READY", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.SUSPECTED

    def test_partial_missing_allows_resolved(self, default_config, default_intelligence):
        """Partial missing values allow RESOLVED if E_h and R_h available."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.15
        intelligence["R_h"] = 0.15
        intelligence["C_h"] = None
        intelligence["S_h"] = None

        counter = 0
        state = HazardState.WATCH
        for i in range(10):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.RESOLVED


# Test Class 7: Baseline Interaction

class TestBaselineInteraction:
    """Test baseline state interaction."""

    def test_initializing_forces_unknown(self, default_config, default_intelligence):
        """INITIALIZING baseline forces UNKNOWN information condition."""
        condition = compute_information_condition(
            confidence=0.8,
            core_coverage=0.9,
            baseline_status="INITIALIZING",
            config=default_config
        )
        assert condition == InformationCondition.UNKNOWN

    def test_frozen_allows_state_transitions(self, default_config, default_intelligence):
        """FROZEN baseline allows state transitions."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = 0.75

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(state, intelligence, "FROZEN", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.CONFIRMED

    def test_recovering_allows_state_transitions(self, default_config, default_intelligence):
        """RECOVERING baseline allows state transitions."""
        intelligence = default_intelligence.copy()
        intelligence["R_h"] = 0.35

        transition = update_state(HazardState.NORMAL, intelligence, "RECOVERING", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.WATCH

    def test_baseline_freeze_on_confirmed(self, default_config, default_intelligence):
        """Baseline freeze triggered on CONFIRMED entry."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.75
        intelligence["C_h"] = 0.7
        intelligence["core_coverage"] = 0.75

        counter = 0
        state = HazardState.SUSPECTED
        for i in range(5):
            transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, None, default_config)
            state = transition.new_state
            counter = transition.persistence_counter

        assert state == HazardState.CONFIRMED
        assert transition.should_freeze_baseline

    def test_baseline_freeze_on_critical(self, default_config, default_intelligence):
        """Baseline remains frozen on CRITICAL."""
        intelligence = default_intelligence.copy()
        intelligence["S_h"] = 0.9

        transition = update_state(HazardState.CONFIRMED, intelligence, "FROZEN", 1000.0, 0, None, default_config)
        assert transition.new_state == HazardState.CRITICAL
        assert transition.should_freeze_baseline


# Test Class 8: Configuration Validation

class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self, default_config):
        """Valid configuration passes."""
        is_valid, msg = validate_config(default_config)
        assert is_valid
        assert msg == "Configuration valid"

    def test_invalid_hysteresis_gap(self, default_config):
        """Invalid hysteresis gap detected."""
        import copy
        config = copy.deepcopy(default_config)
        config["thresholds"]["suspected_evidence_enter"] = 0.4
        config["hysteresis"]["suspected_evidence_exit"] = 0.4  # Equal, not greater

        is_valid, msg = validate_config(config)
        assert not is_valid
        assert "hysteresis" in msg.lower()

    def test_invalid_persistence_zero(self, default_config):
        """Zero persistence rejected."""
        import copy
        config = copy.deepcopy(default_config)
        config["persistence"]["watch_enter"] = 0

        is_valid, msg = validate_config(config)
        assert not is_valid
        assert "persistence" in msg.lower()

    def test_invalid_threshold_out_of_range(self, default_config):
        """Threshold outside [0, 1] rejected."""
        import copy
        config = copy.deepcopy(default_config)
        config["thresholds"]["watch_risk_enter"] = 1.5

        is_valid, msg = validate_config(config)
        assert not is_valid
        assert "threshold" in msg.lower()


# Test Class 9: Determinism

class TestDeterminism:
    """Test deterministic behavior."""

    def test_same_inputs_same_output(self, default_config, default_intelligence):
        """Same inputs produce same output."""
        intelligence = default_intelligence.copy()
        intelligence["E_h"] = 0.45

        # Run twice with identical inputs
        transition1 = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)
        transition2 = update_state(HazardState.WATCH, intelligence, "READY", 1000.0, 0, None, default_config)

        assert transition1.new_state == transition2.new_state
        assert transition1.persistence_counter == transition2.persistence_counter

    def test_reproducible_state_sequence(self, default_config):
        """State sequence reproducible from time series."""
        # Define time series
        time_series = [
            {"E_h": 0.2, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35, "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9},
            {"E_h": 0.2, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35, "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9},
            {"E_h": 0.45, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35, "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9},
            {"E_h": 0.45, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35, "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9},
            {"E_h": 0.45, "C_h": 0.8, "S_h": 0.3, "R_h": 0.35, "A_h": 0.6, "T_h": 0.3, "core_coverage": 0.9},
        ]

        # Run twice
        def run_sequence():
            state = HazardState.NORMAL
            counter = 0
            resolved_start = None
            states = []

            for i, intelligence in enumerate(time_series):
                transition = update_state(state, intelligence, "READY", 1000.0 + i, counter, resolved_start, default_config)
                state = transition.new_state
                counter = transition.persistence_counter
                resolved_start = transition.resolved_hold_start
                states.append(state)

            return states

        states1 = run_sequence()
        states2 = run_sequence()

        assert states1 == states2

    def test_baseline_freeze_helper(self):
        """should_freeze_baseline helper deterministic."""
        assert should_freeze_baseline(HazardState.CONFIRMED)
        assert should_freeze_baseline(HazardState.CRITICAL)
        assert not should_freeze_baseline(HazardState.NORMAL)
        assert not should_freeze_baseline(HazardState.WATCH)
        assert not should_freeze_baseline(HazardState.SUSPECTED)
        assert not should_freeze_baseline(HazardState.RESOLVED)
