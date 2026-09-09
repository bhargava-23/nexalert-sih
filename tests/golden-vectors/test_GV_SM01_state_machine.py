"""
GV-SM01: State machine golden vectors.

Specification: Document 04, Section 10
Validates state machine implementation against deterministic transition scenarios.

PHASE 5 ITERATION 6: Hazard state machine golden vectors.
"""

import json
import pytest
from pathlib import Path

# Import reference implementation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reference" / "python"))

from nexalert_reference.state_machine import (
    HazardState,
    InformationCondition,
    update_state,
    compute_information_condition
)


# Fixture for loading golden vectors
@pytest.fixture
def load_gv():
    """Load golden vector input and expected output."""
    def _load(name: str):
        base_path = Path(__file__).parent
        input_path = base_path / "inputs" / f"{name}.json"
        expected_path = base_path / "expected" / f"{name}.json"

        with open(input_path) as f:
            input_data = json.load(f)
        with open(expected_path) as f:
            expected_data = json.load(f)

        return input_data, expected_data
    return _load


def run_state_sequence(initial_state_str, time_series, config, initial_resolved_hold_start=None):
    """
    Run state machine through time series.

    Args:
        initial_state_str: Initial state as string
        time_series: List of samples with intelligence values
        config: State machine configuration
        initial_resolved_hold_start: Optional timestamp when RESOLVED was entered

    Returns:
        List of state strings, one per sample
    """
    state = HazardState(initial_state_str)
    persistence_counter = 0
    resolved_hold_start = initial_resolved_hold_start

    state_sequence = []

    for sample in time_series:
        transition = update_state(
            current_state=state,
            intelligence=sample,
            baseline_status=sample.get("baseline_status", "READY"),
            timestamp=sample["timestamp"],
            persistence_counter=persistence_counter,
            resolved_hold_start=resolved_hold_start,
            config=config
        )

        state = transition.new_state
        persistence_counter = transition.persistence_counter
        resolved_hold_start = transition.resolved_hold_start
        state_sequence.append(state.value)

    return state_sequence


# Basic Transitions (7 tests)

def test_GV_SM01_normal_to_watch(load_gv):
    """GV-SM01-01: NORMAL → WATCH transition via risk threshold."""
    input_data, expected_data = load_gv("GV_SM01_normal_to_watch")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_watch_to_suspected(load_gv):
    """GV-SM01-02: WATCH → SUSPECTED with persistence."""
    input_data, expected_data = load_gv("GV_SM01_watch_to_suspected")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_suspected_to_confirmed(load_gv):
    """GV-SM01-03: SUSPECTED → CONFIRMED with high evidence + confidence."""
    input_data, expected_data = load_gv("GV_SM01_suspected_to_confirmed")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_confirmed_to_critical(load_gv):
    """GV-SM01-04: CONFIRMED → CRITICAL due to severe conditions."""
    input_data, expected_data = load_gv("GV_SM01_confirmed_to_critical")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_critical_to_resolved(load_gv):
    """GV-SM01-05: CRITICAL → RESOLVED when conditions subside."""
    input_data, expected_data = load_gv("GV_SM01_critical_to_resolved")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_resolved_to_normal(load_gv):
    """GV-SM01-06: RESOLVED → NORMAL after hold period complete."""
    input_data, expected_data = load_gv("GV_SM01_resolved_to_normal")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"],
        input_data.get("resolved_hold_start")
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_full_deescalation(load_gv):
    """GV-SM01-07: Full de-escalation path."""
    input_data, expected_data = load_gv("GV_SM01_full_deescalation")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# Hysteresis (4 tests)

def test_GV_SM01_hysteresis_watch(load_gv):
    """GV-SM01-08: Hysteresis prevents watch flapping."""
    input_data, expected_data = load_gv("GV_SM01_hysteresis_watch")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_hysteresis_confirmed(load_gv):
    """GV-SM01-09: Confirmed hysteresis gap."""
    input_data, expected_data = load_gv("GV_SM01_hysteresis_confirmed")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_hysteresis_critical(load_gv):
    """GV-SM01-10: Critical hysteresis boundary."""
    input_data, expected_data = load_gv("GV_SM01_hysteresis_critical")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_hysteresis_prevents_flapping(load_gv):
    """GV-SM01-11: Hysteresis prevents state flapping."""
    input_data, expected_data = load_gv("GV_SM01_hysteresis_prevents_flapping")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# Persistence (5 tests)

def test_GV_SM01_persistence_suspected(load_gv):
    """GV-SM01-12: 3-sample persistence for SUSPECTED."""
    input_data, expected_data = load_gv("GV_SM01_persistence_suspected")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_persistence_confirmed(load_gv):
    """GV-SM01-13: 5-sample persistence for CONFIRMED."""
    input_data, expected_data = load_gv("GV_SM01_persistence_confirmed")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_persistence_reset(load_gv):
    """GV-SM01-14: Persistence counter resets when criteria not met."""
    input_data, expected_data = load_gv("GV_SM01_persistence_reset")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_persistence_resolved(load_gv):
    """GV-SM01-15: 10-sample persistence for RESOLVED."""
    input_data, expected_data = load_gv("GV_SM01_persistence_resolved")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_fast_escalation(load_gv):
    """GV-SM01-16: Fast path WATCH → CONFIRMED (2 samples)."""
    input_data, expected_data = load_gv("GV_SM01_fast_escalation")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# RESOLVED (3 tests)

def test_GV_SM01_resolved_hold(load_gv):
    """GV-SM01-17: RESOLVED hold period (5 minutes)."""
    input_data, expected_data = load_gv("GV_SM01_resolved_hold")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"],
        input_data.get("resolved_hold_start")
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_resolved_reescalation(load_gv):
    """GV-SM01-18: Re-escalation during RESOLVED hold."""
    input_data, expected_data = load_gv("GV_SM01_resolved_reescalation")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"],
        input_data.get("resolved_hold_start")
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_resolved_from_critical(load_gv):
    """GV-SM01-19: RESOLVED entry from CRITICAL state."""
    input_data, expected_data = load_gv("GV_SM01_resolved_from_critical")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# Information Condition (4 tests)

def test_GV_SM01_degraded_confirmed(load_gv):
    """GV-SM01-20: CONFIRMED + DEGRADED information condition."""
    input_data, expected_data = load_gv("GV_SM01_degraded_confirmed")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_unknown_blocks_new_confirmed(load_gv):
    """GV-SM01-21: UNKNOWN blocks NEW CONFIRMED declaration."""
    input_data, expected_data = load_gv("GV_SM01_unknown_blocks_new_confirmed")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_unknown_initializing(load_gv):
    """GV-SM01-22: UNKNOWN during baseline INITIALIZING."""
    input_data, expected_data = load_gv("GV_SM01_unknown_initializing")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_fast_path_blocked_unknown(load_gv):
    """GV-SM01-23: Fast path WATCH → CONFIRMED blocked under UNKNOWN."""
    input_data, expected_data = load_gv("GV_SM01_fast_path_blocked_unknown")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# Missing Values (2 tests)

def test_GV_SM01_missing_evidence(load_gv):
    """GV-SM01-24: E_h = None blocks SUSPECTED transition."""
    input_data, expected_data = load_gv("GV_SM01_missing_evidence")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


def test_GV_SM01_missing_severity(load_gv):
    """GV-SM01-25: S_h = None blocks CRITICAL transition."""
    input_data, expected_data = load_gv("GV_SM01_missing_severity")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]


# Multi-Hazard (1 test)

def test_GV_SM01_multi_hazard(load_gv):
    """GV-SM01-26: Multi-hazard independence (fire and flood)."""
    input_data, expected_data = load_gv("GV_SM01_multi_hazard")

    # Run fire sequence
    fire_sequence = run_state_sequence(
        input_data["fire_initial_state"],
        input_data["fire_time_series"],
        input_data["config"]
    )

    # Run flood sequence
    flood_sequence = run_state_sequence(
        input_data["flood_initial_state"],
        input_data["flood_time_series"],
        input_data["config"]
    )

    assert fire_sequence == expected_data["fire_state_sequence"]
    assert flood_sequence == expected_data["flood_state_sequence"]
    assert fire_sequence[-1] == expected_data["fire_final_state"]
    assert flood_sequence[-1] == expected_data["flood_final_state"]


# Fast Path Information Gate Blocking (1 test)

def test_GV_SM01_fast_suspected_critical_blocked(load_gv):
    """GV-SM01-27: Fast SUSPECTED → CRITICAL blocked under UNKNOWN."""
    input_data, expected_data = load_gv("GV_SM01_fast_suspected_critical_blocked")

    state_sequence = run_state_sequence(
        input_data["initial_state"],
        input_data["time_series"],
        input_data["config"]
    )

    assert state_sequence == expected_data["state_sequence"]
    assert state_sequence[-1] == expected_data["final_state"]
