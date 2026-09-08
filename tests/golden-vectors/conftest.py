"""
Golden vector test infrastructure.

Loads test inputs/expected outputs from JSON files.
Provides tolerance-checking assertions.

Specification: Document 17, Section 4
"""
import pytest
import json
import numpy as np
from pathlib import Path

GOLDEN_VECTORS_DIR = Path(__file__).parent


def load_golden_vector(vector_id: str):
    """Load golden vector inputs and expected outputs."""
    input_file = GOLDEN_VECTORS_DIR / "inputs" / f"{vector_id}.json"
    expected_file = GOLDEN_VECTORS_DIR / "expected" / f"{vector_id}.json"

    with open(input_file) as f:
        inputs = json.load(f)
    with open(expected_file) as f:
        expected = json.load(f)

    return inputs, expected


def assert_close(actual, expected, rtol=1e-6, atol=1e-9, label=""):
    """
    Assert numerical values close within tolerance.

    Uses numpy.allclose semantics: |actual - expected| <= atol + rtol * |expected|
    """
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{label}: Expected {expected}, got {actual} "
            f"(diff={abs(actual - expected)}, rtol={rtol}, atol={atol})"
        )


@pytest.fixture
def load_gv():
    """Fixture to load golden vectors."""
    return load_golden_vector


@pytest.fixture
def assert_close_fixture():
    """Fixture for tolerance checking."""
    return assert_close
