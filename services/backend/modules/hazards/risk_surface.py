"""Risk surface generation for Track C

CRITICAL: Risk surface is a continuous operational index, NOT probability.
Risk surface is DISTINCT from physical fire footprint.

Computes operational risk based on:
- Arrival-time gradients (how soon fire arrives)
- Spatial decay from fire geometry
- Continuous [0, 1] risk index
"""
from typing import Optional
import numpy as np
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Polygon, MultiPolygon, Point


def compute_risk_from_arrival_time(
    arrival_time: np.ndarray,
    current_time: float,
    max_horizon_minutes: float = 180.0,
    decay_rate: float = 0.02
) -> np.ndarray:
    """Compute risk surface from arrival-time field

    Risk based on how soon fire is predicted to arrive:
    - Imminent arrival → high risk
    - Distant arrival → lower risk
    - Not reached → zero risk

    Args:
        arrival_time: Arrival time field (minutes, np.inf = not reached)
        current_time: Current simulation time (minutes)
        max_horizon_minutes: Maximum horizon for risk computation
        decay_rate: Exponential decay rate (higher = faster decay)

    Returns:
        Risk surface [0, 1]
    """
    # Time until fire arrives
    time_until_arrival = arrival_time - current_time

    # Risk only for future arrivals within horizon
    valid_mask = (time_until_arrival > 0) & (time_until_arrival <= max_horizon_minutes)

    # Initialize risk surface
    risk = np.zeros_like(arrival_time, dtype=np.float32)

    # Exponential decay: risk = exp(-decay_rate * time_until_arrival)
    # Imminent arrival (small time) → risk near 1.0
    # Distant arrival (large time) → risk near 0.0
    risk[valid_mask] = np.exp(-decay_rate * time_until_arrival[valid_mask])

    # Clip to [0, 1]
    risk = np.clip(risk, 0.0, 1.0)

    return risk


def compute_risk_from_geometry(
    geometry: Polygon | MultiPolygon,
    grid_shape: tuple,
    origin_x: float,
    origin_y: float,
    cell_size_m: float,
    max_distance_m: float = 5000.0,
    decay_rate: float = 0.0005
) -> np.ndarray:
    """Compute risk surface from fire geometry

    Risk based on distance from fire perimeter:
    - Inside fire → risk = 1.0
    - Near fire → high risk (exponential decay)
    - Far from fire → zero risk

    Args:
        geometry: Fire geometry (Polygon or MultiPolygon)
        grid_shape: (rows, cols) of output grid
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters
        max_distance_m: Maximum distance for risk computation
        decay_rate: Exponential decay rate

    Returns:
        Risk surface [0, 1]
    """
    rows, cols = grid_shape

    # Initialize risk surface
    risk = np.zeros((rows, cols), dtype=np.float32)

    if geometry.is_empty:
        return risk

    # Create grid of cell centers
    for i in range(rows):
        for j in range(cols):
            # Cell center coordinates
            x = origin_x + (j + 0.5) * cell_size_m
            y = origin_y - (i + 0.5) * cell_size_m

            point = Point(x, y)

            # Check if inside fire
            if geometry.contains(point):
                risk[i, j] = 1.0
                continue

            # Distance to fire perimeter
            distance = geometry.distance(point)

            if distance <= max_distance_m:
                # Exponential decay: risk = exp(-decay_rate * distance)
                risk[i, j] = np.exp(-decay_rate * distance)

    # Clip to [0, 1]
    risk = np.clip(risk, 0.0, 1.0)

    return risk


def combine_risk_surfaces(
    risk_surfaces: list,
    weights: Optional[list] = None
) -> np.ndarray:
    """Combine multiple risk surfaces

    Args:
        risk_surfaces: List of risk arrays [0, 1]
        weights: Optional weights for each surface (default: equal)

    Returns:
        Combined risk surface [0, 1]
    """
    if not risk_surfaces:
        raise ValueError("No risk surfaces provided")

    if weights is None:
        weights = [1.0] * len(risk_surfaces)

    if len(weights) != len(risk_surfaces):
        raise ValueError("Number of weights must match number of surfaces")

    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    normalized_weights = [w / total_weight for w in weights]

    # Weighted sum
    combined = np.zeros_like(risk_surfaces[0], dtype=np.float32)
    for surface, weight in zip(risk_surfaces, normalized_weights):
        combined += weight * surface

    # Clip to [0, 1]
    combined = np.clip(combined, 0.0, 1.0)

    return combined


def smooth_risk_surface(
    risk: np.ndarray,
    sigma: float = 2.0
) -> np.ndarray:
    """Smooth risk surface using Gaussian filter

    Args:
        risk: Risk surface [0, 1]
        sigma: Gaussian kernel standard deviation (cells)

    Returns:
        Smoothed risk surface [0, 1]
    """
    from scipy.ndimage import gaussian_filter

    smoothed = gaussian_filter(risk, sigma=sigma, mode='constant', cval=0.0)

    # Clip to [0, 1]
    smoothed = np.clip(smoothed, 0.0, 1.0)

    return smoothed


def risk_statistics(risk: np.ndarray) -> dict:
    """Compute risk surface statistics

    Args:
        risk: Risk surface [0, 1]

    Returns:
        Statistics dict
    """
    # Cells with non-zero risk
    nonzero_mask = risk > 0.0
    nonzero_count = np.sum(nonzero_mask)
    total_count = risk.size

    if nonzero_count > 0:
        max_risk = float(np.max(risk))
        mean_risk = float(np.mean(risk[nonzero_mask]))
        median_risk = float(np.median(risk[nonzero_mask]))

        # Risk level counts
        high_risk_count = np.sum(risk >= 0.7)
        medium_risk_count = np.sum((risk >= 0.3) & (risk < 0.7))
        low_risk_count = np.sum((risk > 0.0) & (risk < 0.3))
    else:
        max_risk = mean_risk = median_risk = 0.0
        high_risk_count = medium_risk_count = low_risk_count = 0

    return {
        "max_risk": max_risk,
        "mean_risk_nonzero": mean_risk,
        "median_risk_nonzero": median_risk,
        "cells_at_risk": int(nonzero_count),
        "cells_total": int(total_count),
        "fraction_at_risk": float(nonzero_count) / total_count if total_count > 0 else 0.0,
        "high_risk_cells": int(high_risk_count),
        "medium_risk_cells": int(medium_risk_count),
        "low_risk_cells": int(low_risk_count),
    }


def serialize_risk_surface(
    risk: np.ndarray,
    origin_x: float,
    origin_y: float,
    cell_size_m: float,
    compression: str = "none"
) -> dict:
    """Serialize risk surface for database storage

    Args:
        risk: Risk surface [0, 1]
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters
        compression: Compression method ("none", "sparse")

    Returns:
        Serialized risk surface dict (JSONB-compatible)
    """
    rows, cols = risk.shape

    if compression == "sparse":
        # Sparse representation: only non-zero cells
        nonzero_indices = np.argwhere(risk > 0.0)
        sparse_data = []

        for idx in nonzero_indices:
            i, j = idx
            sparse_data.append({
                "i": int(i),
                "j": int(j),
                "risk": float(risk[i, j])
            })

        serialized = {
            "format": "sparse",
            "rows": int(rows),
            "cols": int(cols),
            "origin_x": float(origin_x),
            "origin_y": float(origin_y),
            "cell_size_m": float(cell_size_m),
            "data": sparse_data,
        }
    else:
        # Dense representation: full grid
        # Convert to list for JSON serialization
        risk_list = risk.tolist()

        serialized = {
            "format": "dense",
            "rows": int(rows),
            "cols": int(cols),
            "origin_x": float(origin_x),
            "origin_y": float(origin_y),
            "cell_size_m": float(cell_size_m),
            "data": risk_list,
        }

    return serialized


def deserialize_risk_surface(serialized: dict) -> tuple:
    """Deserialize risk surface from database

    Args:
        serialized: Serialized risk surface dict

    Returns:
        (risk, origin_x, origin_y, cell_size_m)
    """
    format_type = serialized.get("format", "dense")
    rows = serialized["rows"]
    cols = serialized["cols"]
    origin_x = serialized["origin_x"]
    origin_y = serialized["origin_y"]
    cell_size_m = serialized["cell_size_m"]

    if format_type == "sparse":
        # Reconstruct from sparse representation
        risk = np.zeros((rows, cols), dtype=np.float32)
        for entry in serialized["data"]:
            i = entry["i"]
            j = entry["j"]
            risk[i, j] = entry["risk"]
    else:
        # Dense representation
        risk = np.array(serialized["data"], dtype=np.float32)

    return risk, origin_x, origin_y, cell_size_m
