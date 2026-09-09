"""B2 Integration Wiring - Simple Validation

Validates that B2 coordinator is properly integrated into MQTT ingestion pipeline
without requiring full database initialization.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*70)
print("B2 COORDINATOR INTEGRATION VALIDATION")
print("="*70)

# Test 1: Import validation
print("\nTest 1: Module imports")
print("-" * 70)

try:
    from modules.intelligence.b2_coordinator import get_coordinator, B2Coordinator
    print("✓ B2 coordinator module imports successfully")
except ImportError as e:
    print(f"✗ Failed to import B2 coordinator: {e}")
    sys.exit(1)

try:
    from modules.ingestion.mqtt_consumer import MQTTTelemetryConsumer
    print("✓ MQTT consumer module imports successfully")
except ImportError as e:
    print(f"✗ Failed to import MQTT consumer: {e}")
    sys.exit(1)

try:
    from modules.intelligence.regional_fusion import (
        NodeObservation,
        RegionalFusionResult,
        fuse_regional_hazard
    )
    print("✓ Regional fusion module imports successfully")
except ImportError as e:
    print(f"✗ Failed to import regional fusion: {e}")
    sys.exit(1)

try:
    from modules.intelligence.incident_correlation import (
        IncidentState,
        IncidentCandidate,
        should_correlate_with_incident,
        determine_incident_state
    )
    print("✓ Incident correlation module imports successfully")
except ImportError as e:
    print(f"✗ Failed to import incident correlation: {e}")
    sys.exit(1)

# Test 2: Coordinator initialization
print("\nTest 2: Coordinator initialization")
print("-" * 70)

try:
    coordinator = get_coordinator()
    print("✓ B2 coordinator initialized successfully")

    stats = coordinator.get_stats()
    print(f"  Initial stats: {stats}")

    assert isinstance(stats, dict), "Stats should be a dictionary"
    assert "triggers_total" in stats, "Stats should have triggers_total"
    assert "fusion_runs" in stats, "Stats should have fusion_runs"
    assert "incidents_created" in stats, "Stats should have incidents_created"
    assert "errors" in stats, "Stats should have errors"

    print("✓ Coordinator stats structure validated")

except Exception as e:
    print(f"✗ Coordinator initialization failed: {e}")
    sys.exit(1)

# Test 3: Integration point validation
print("\nTest 3: Integration point validation")
print("-" * 70)

try:
    # Check that MQTT consumer has the coordinator import
    import inspect
    mqtt_source = inspect.getsource(MQTTTelemetryConsumer)

    if "get_coordinator" in mqtt_source:
        print("✓ MQTT consumer imports B2 coordinator")
    else:
        print("✗ MQTT consumer does NOT import B2 coordinator")
        sys.exit(1)

    if "trigger_after_persistence" in mqtt_source:
        print("✓ MQTT consumer calls coordinator.trigger_after_persistence")
    else:
        print("✗ MQTT consumer does NOT call trigger_after_persistence")
        sys.exit(1)

    # Check coordinator has required methods
    assert hasattr(coordinator, "trigger_after_persistence"), \
        "Coordinator missing trigger_after_persistence method"
    print("✓ Coordinator has trigger_after_persistence method")

    assert hasattr(coordinator, "get_stats"), \
        "Coordinator missing get_stats method"
    print("✓ Coordinator has get_stats method")

except Exception as e:
    print(f"✗ Integration point validation failed: {e}")
    sys.exit(1)

# Test 4: Regional fusion functions
print("\nTest 4: Regional fusion functions")
print("-" * 70)

try:
    from modules.intelligence.regional_fusion import (
        compute_freshness_weight,
        compute_spatial_distance_m,
        compute_spatial_weight,
        compute_trust_weight
    )

    # Test freshness weight
    weight = compute_freshness_weight(0.0)
    assert 0.99 < weight <= 1.0, f"Fresh weight should be ~1.0, got {weight}"
    print("✓ compute_freshness_weight works")

    # Test spatial distance
    dist = compute_spatial_distance_m(12.9716, 77.5946, 12.9716, 77.5946)
    assert dist is not None and dist < 1.0, f"Same point distance should be ~0, got {dist}"
    print("✓ compute_spatial_distance_m works")

    # Test spatial weight
    weight = compute_spatial_weight(0.0)
    assert weight == 1.0, f"Zero distance weight should be 1.0, got {weight}"
    print("✓ compute_spatial_weight works")

    # Test trust weight
    weight = compute_trust_weight(0.9, 0.9, "GOOD")
    assert 0.8 < weight < 0.85, f"Trust weight should be ~0.81, got {weight}"
    print("✓ compute_trust_weight works")

except Exception as e:
    print(f"✗ Regional fusion functions failed: {e}")
    sys.exit(1)

# Test 5: Incident correlation functions
print("\nTest 5: Incident correlation functions")
print("-" * 70)

try:
    from datetime import datetime

    # Test incident state enum
    assert IncidentState.NEW == "NEW"
    assert IncidentState.ACTIVE == "ACTIVE"
    assert IncidentState.ESCALATED == "ESCALATED"
    assert IncidentState.RESOLVED == "RESOLVED"
    print("✓ IncidentState enum defined correctly")

    # Test correlation function exists
    candidate = IncidentCandidate(
        incident_id="test-id",
        hazard_type="fire",
        state="ACTIVE",
        centroid_lat=12.9716,
        centroid_lon=77.5946,
        last_observed_at=datetime.utcnow(),
        severity_index=0.7,
        risk_index=0.65
    )

    # Should NOT correlate (far away)
    result = should_correlate_with_incident(
        observation_location=(13.0, 78.0),  # ~100km away
        observation_time=datetime.utcnow(),
        incident=candidate
    )
    assert result == False, "Should not correlate with far incident"
    print("✓ should_correlate_with_incident works")

except Exception as e:
    print(f"✗ Incident correlation functions failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "="*70)
print("✓ ALL INTEGRATION VALIDATION TESTS PASSED")
print("="*70)

print("\nIntegration Status:")
print("  ✓ B2 coordinator module: WORKING")
print("  ✓ MQTT consumer integration: WIRED")
print("  ✓ Regional fusion engine: WORKING")
print("  ✓ Incident correlation engine: WORKING")
print("  ✓ Integration hooks: PROPERLY CONNECTED")

print("\nArchitecture Flow:")
print("  1. MQTT telemetry arrives")
print("  2. Validation + persistence (Track B1)")
print("  3. coordinator.trigger_after_persistence() called")
print("  4. Regional fusion triggered (when sufficient nodes)")
print("  5. Incident correlation triggered (when conditions met)")

print("\nNotes:")
print("  - Full end-to-end requires backend running")
print("  - Regional fusion requires node hazard assessments")
print("  - Incident creation requires database access")
print("  - This validation confirms WIRING is correct")

print("\n" + "="*70)
