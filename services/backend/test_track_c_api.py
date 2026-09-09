"""Test Track C API endpoints"""
import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_api_endpoints():
    """Test all Track C API endpoints"""

    print("=" * 60)
    print("TRACK C API ENDPOINT TESTS")
    print("=" * 60)

    # Test 1: POST /api/simulations/start (simulate fire spread)
    print("\n1. POST /api/simulations/start")
    print("-" * 60)

    simulation_request = {
        "ignition_lat": 12.9716,
        "ignition_lon": 77.5946,
        "simulation_type": "SIMULATION",
        "environmental_params": {
            "fuel_type": "uniform_grass",
            "moisture_index": 0.3,
            "wind_speed_ms": 5.0,
            "wind_from_deg": 270.0,
            "dem_type": "flat"
        },
        "domain_size_m": 5000.0,
        "cell_size_m": 50.0,
        "max_time_minutes": 60.0
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/simulations/start",
            json=simulation_request,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            simulation_id = result.get("simulation_id")
            print(f"  ✓ Status: {response.status_code}")
            print(f"  ✓ Simulation ID: {simulation_id}")
            print(f"  ✓ Type: {result.get('simulation_type')}")
            print(f"  ✓ Response keys: {list(result.keys())}")
        else:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  ✗ Error: {response.text}")
            return None

    except Exception as e:
        print(f"  ✗ Request failed: {str(e)}")
        return None

    # Test 2: GET /api/simulations/{simulation_id}/geometries
    print("\n2. GET /api/simulations/{simulation_id}/geometries")
    print("-" * 60)

    try:
        response = requests.get(
            f"{BASE_URL}/api/simulations/{simulation_id}/geometries",
            timeout=10
        )

        if response.status_code == 200:
            geometries = response.json()
            print(f"  ✓ Status: {response.status_code}")
            print(f"  ✓ Geometries returned: {len(geometries)}")

            for geom in geometries:
                zone_type = geom.get("zone_type")
                area_ha = geom.get("area_hectares", 0)
                print(f"    - {zone_type}: {area_ha:.2f} hectares")
        else:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  ✗ Error: {response.text}")

    except Exception as e:
        print(f"  ✗ Request failed: {str(e)}")

    # Test 3: GET /api/simulations (list simulations)
    print("\n3. GET /api/simulations (list)")
    print("-" * 60)

    try:
        response = requests.get(
            f"{BASE_URL}/api/simulations?limit=10",
            timeout=10
        )

        if response.status_code == 200:
            simulations = response.json()
            print(f"  ✓ Status: {response.status_code}")
            print(f"  ✓ Simulations found: {len(simulations)}")

            for sim in simulations:
                sim_id = sim.get("simulation_id")
                sim_type = sim.get("simulation_type")
                print(f"    - {sim_id}: {sim_type}")
        else:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  ✗ Error: {response.text}")

    except Exception as e:
        print(f"  ✗ Request failed: {str(e)}")

    # Test 4: Health check
    print("\n4. GET /health")
    print("-" * 60)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            health = response.json()
            print(f"  ✓ Status: {response.status_code}")
            print(f"  ✓ Response: {health}")
        else:
            print(f"  ✗ Status: {response.status_code}")

    except Exception as e:
        print(f"  ✗ Request failed: {str(e)}")

    print("\n" + "=" * 60)
    print("TRACK C API TESTS COMPLETE")
    print("=" * 60)

    return simulation_id


if __name__ == "__main__":
    test_api_endpoints()
