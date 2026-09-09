"""Track B2 multi-node validation scenarios

Test scenarios for Master/Regional Intelligence validation.
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

def generate_node_observations_scenario_1():
    """Scenario 1: Single healthy node with anomalous reading

    Expected: Local hazard only, no regional incident created
    """
    base_time = datetime.utcnow()

    observations = [
        {
            "node_id": "NODE-001",
            "hazard_type": "fire",
            "state": "SUSPECTED",
            "evidence": 0.45,
            "confidence": 0.75,
            "severity": 0.3,
            "risk": 0.35,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.85
        }
    ]

    return {
        "scenario": "single_node_anomaly",
        "description": "One healthy node with anomalous reading",
        "expected": "Local hazard only, no regional incident",
        "observations": observations
    }


def generate_node_observations_scenario_2():
    """Scenario 2: 2-3 nearby nodes showing consistent hazard

    Expected: Correlated regional incident created
    """
    base_time = datetime.utcnow()

    # Three nodes within 50m of each other
    observations = [
        {
            "node_id": "NODE-002",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.75,
            "confidence": 0.82,
            "severity": 0.65,
            "risk": 0.7,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.88
        },
        {
            "node_id": "NODE-003",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.78,
            "confidence": 0.85,
            "severity": 0.68,
            "risk": 0.72,
            "information_condition": "GOOD",
            "observation_time": (base_time + timedelta(seconds=10)).isoformat(),
            "location_lat": 12.9717,  # ~30m away
            "location_lon": 77.5947,
            "node_reliability": 0.90
        },
        {
            "node_id": "NODE-004",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.72,
            "confidence": 0.80,
            "severity": 0.62,
            "risk": 0.68,
            "information_condition": "GOOD",
            "observation_time": (base_time + timedelta(seconds=15)).isoformat(),
            "location_lat": 12.9718,  # ~40m away
            "location_lon": 77.5948,
            "node_reliability": 0.87
        }
    ]

    return {
        "scenario": "multi_node_correlated",
        "description": "Multiple nearby nodes with consistent fire detection",
        "expected": "Regional incident created, state=ACTIVE",
        "observations": observations
    }


def generate_node_observations_scenario_3():
    """Scenario 3: Conflicting node evidence

    Expected: Do not erase valid local hazard
    """
    base_time = datetime.utcnow()

    observations = [
        {
            "node_id": "NODE-005",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.80,
            "confidence": 0.85,
            "severity": 0.70,
            "risk": 0.75,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.88
        },
        {
            "node_id": "NODE-006",
            "hazard_type": "fire",
            "state": "NORMAL",
            "evidence": 0.10,
            "confidence": 0.70,
            "severity": 0.05,
            "risk": 0.08,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9717,  # Nearby but disagrees
            "location_lon": 77.5947,
            "node_reliability": 0.85
        }
    ]

    return {
        "scenario": "conflicting_nodes",
        "description": "One node CONFIRMED, nearby node NORMAL",
        "expected": "Both local states preserved, regional fusion reflects mixed evidence",
        "observations": observations
    }


def generate_node_observations_scenario_4():
    """Scenario 4: Stale node data

    Expected: Reduced influence in regional fusion
    """
    base_time = datetime.utcnow()

    observations = [
        {
            "node_id": "NODE-007",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.75,
            "confidence": 0.82,
            "severity": 0.65,
            "risk": 0.70,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),  # Fresh
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.88
        },
        {
            "node_id": "NODE-008",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.85,
            "confidence": 0.88,
            "severity": 0.75,
            "risk": 0.80,
            "information_condition": "GOOD",
            "observation_time": (base_time - timedelta(minutes=10)).isoformat(),  # Stale
            "location_lat": 12.9717,
            "location_lon": 77.5947,
            "node_reliability": 0.90
        }
    ]

    return {
        "scenario": "stale_node_data",
        "description": "One fresh node, one stale (10 minutes old)",
        "expected": "Fresh node dominates regional fusion, stale node has reduced weight",
        "observations": observations
    }


def generate_node_observations_scenario_5():
    """Scenario 5: Disconnected/unhealthy node

    Expected: Distinguish from normal environmental state
    """
    base_time = datetime.utcnow()

    observations = [
        {
            "node_id": "NODE-009",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.78,
            "confidence": 0.50,  # Low confidence
            "severity": 0.68,
            "risk": 0.72,
            "information_condition": "DEGRADED",  # Degraded information
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.30  # Low reliability
        }
    ]

    return {
        "scenario": "unhealthy_node",
        "description": "Node with low reliability and degraded information condition",
        "expected": "Regional fusion reduces trust weight, incident may not escalate",
        "observations": observations
    }


def generate_node_observations_scenario_6():
    """Scenario 6: Duplicate/repeated observations

    Expected: No duplicate incident, idempotent handling
    """
    base_time = datetime.utcnow()

    # Same observation reported twice
    observation = {
        "node_id": "NODE-010",
        "hazard_type": "fire",
        "state": "CONFIRMED",
        "evidence": 0.75,
        "confidence": 0.82,
        "severity": 0.65,
        "risk": 0.70,
        "information_condition": "GOOD",
        "observation_time": base_time.isoformat(),
        "location_lat": 12.9716,
        "location_lon": 77.5946,
        "node_reliability": 0.88
    }

    observations = [observation, observation]  # Same observation twice

    return {
        "scenario": "duplicate_observations",
        "description": "Same observation reported multiple times",
        "expected": "Idempotent handling, single incident created",
        "observations": observations
    }


def generate_node_observations_scenario_7():
    """Scenario 7: Incident resolution across nodes

    Expected: Incident resolves when all nodes show resolution
    """
    base_time = datetime.utcnow()

    # Initial: Multiple nodes CONFIRMED
    initial_observations = [
        {
            "node_id": "NODE-011",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.75,
            "confidence": 0.82,
            "severity": 0.65,
            "risk": 0.70,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.88
        },
        {
            "node_id": "NODE-012",
            "hazard_type": "fire",
            "state": "CONFIRMED",
            "evidence": 0.72,
            "confidence": 0.80,
            "severity": 0.62,
            "risk": 0.68,
            "information_condition": "GOOD",
            "observation_time": base_time.isoformat(),
            "location_lat": 12.9717,
            "location_lon": 77.5947,
            "node_reliability": 0.87
        }
    ]

    # Later: All nodes RESOLVED
    resolved_observations = [
        {
            "node_id": "NODE-011",
            "hazard_type": "fire",
            "state": "RESOLVED",
            "evidence": 0.15,
            "confidence": 0.75,
            "severity": 0.10,
            "risk": 0.12,
            "information_condition": "GOOD",
            "observation_time": (base_time + timedelta(minutes=30)).isoformat(),
            "location_lat": 12.9716,
            "location_lon": 77.5946,
            "node_reliability": 0.88
        },
        {
            "node_id": "NODE-012",
            "hazard_type": "fire",
            "state": "RESOLVED",
            "evidence": 0.12,
            "confidence": 0.78,
            "severity": 0.08,
            "risk": 0.10,
            "information_condition": "GOOD",
            "observation_time": (base_time + timedelta(minutes=30)).isoformat(),
            "location_lat": 12.9717,
            "location_lon": 77.5947,
            "node_reliability": 0.87
        }
    ]

    return {
        "scenario": "incident_resolution",
        "description": "Multiple nodes CONFIRMED then all RESOLVED",
        "expected": "Incident state transitions to RESOLVED",
        "initial_observations": initial_observations,
        "resolved_observations": resolved_observations
    }


def save_all_scenarios():
    """Save all test scenarios to JSON files"""
    scenarios = [
        generate_node_observations_scenario_1(),
        generate_node_observations_scenario_2(),
        generate_node_observations_scenario_3(),
        generate_node_observations_scenario_4(),
        generate_node_observations_scenario_5(),
        generate_node_observations_scenario_6(),
        generate_node_observations_scenario_7()
    ]

    for i, scenario in enumerate(scenarios, 1):
        filename = f"scenario_{i}_{scenario['scenario']}.json"
        with open(filename, 'w') as f:
            json.dump(scenario, f, indent=2)
        print(f"Saved: {filename}")


if __name__ == "__main__":
    save_all_scenarios()
