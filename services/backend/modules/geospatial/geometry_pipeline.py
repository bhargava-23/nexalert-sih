"""Geometry pipeline for Track C

Converts arrival-time raster to fire geometry:
- Threshold selection (current/warning/projection zones)
- Connected component analysis
- Rasterio polygonization
- Geometry repair (shapely.make_valid)
- Polygon/MultiPolygon support
"""
from typing import Tuple, List, Optional
import numpy as np
from scipy import ndimage
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.validation import make_valid
import rasterio.features


def threshold_arrival_time(
    arrival_time: np.ndarray,
    current_time: float,
    warning_horizon_minutes: float,
    projection_horizon_minutes: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create zone masks from arrival-time field

    Zones:
    - CURRENT: T_a(c) <= current_time
    - WARNING: current_time < T_a(c) <= current_time + warning_horizon
    - PROJECTION: current_time + warning_horizon < T_a(c) <= current_time + projection_horizon

    Args:
        arrival_time: Arrival time field (minutes, np.inf = not reached)
        current_time: Current simulation time (minutes)
        warning_horizon_minutes: Warning zone horizon (e.g., 30 minutes)
        projection_horizon_minutes: Projection zone horizon (e.g., 120 minutes)

    Returns:
        (current_mask, warning_mask, projection_mask) boolean arrays
    """
    # CURRENT zone: already burned
    current_mask = arrival_time <= current_time

    # WARNING zone: near future
    warning_end = current_time + warning_horizon_minutes
    warning_mask = (arrival_time > current_time) & (arrival_time <= warning_end)

    # PROJECTION zone: longer future
    projection_end = current_time + projection_horizon_minutes
    projection_mask = (arrival_time > warning_end) & (arrival_time <= projection_end)

    return current_mask, warning_mask, projection_mask


def connected_components(mask: np.ndarray) -> Tuple[np.ndarray, int]:
    """Label connected components in binary mask

    Uses 8-connectivity (includes diagonal neighbors).

    Args:
        mask: Boolean mask

    Returns:
        (labels, num_components)
        - labels: Array with component labels (0 = background)
        - num_components: Number of connected components
    """
    structure = np.ones((3, 3), dtype=int)  # 8-connectivity
    labels, num_components = ndimage.label(mask, structure=structure)
    return labels, num_components


def raster_to_polygons(
    mask: np.ndarray,
    transform: rasterio.Affine
) -> List[Polygon]:
    """Polygonize raster mask using rasterio

    Args:
        mask: Boolean mask
        transform: Affine transform (rasterio)

    Returns:
        List of Polygon geometries
    """
    # Convert boolean to uint8 (rasterio requires integer)
    mask_uint8 = mask.astype(np.uint8)

    # Polygonize
    polygons = []
    for geom, value in rasterio.features.shapes(mask_uint8, transform=transform):
        if value == 1:  # Foreground
            poly = shape(geom)
            polygons.append(poly)

    return polygons


def repair_geometry(geom) -> Polygon | MultiPolygon:
    """Repair invalid geometry using shapely.make_valid

    Args:
        geom: Shapely geometry (Polygon or MultiPolygon)

    Returns:
        Valid Polygon or MultiPolygon
    """
    if not geom.is_valid:
        geom = make_valid(geom)

    return geom


def merge_polygons(polygons: List[Polygon]) -> Polygon | MultiPolygon:
    """Merge list of polygons into single geometry

    Args:
        polygons: List of Polygon objects

    Returns:
        Merged Polygon or MultiPolygon
    """
    if not polygons:
        return MultiPolygon([])

    if len(polygons) == 1:
        return repair_geometry(polygons[0])

    # Union all polygons
    from shapely.ops import unary_union
    merged = unary_union(polygons)

    return repair_geometry(merged)


def create_affine_transform(
    origin_x: float,
    origin_y: float,
    cell_size_m: float
) -> rasterio.Affine:
    """Create affine transform for raster

    Args:
        origin_x: Grid origin X (meters, top-left)
        origin_y: Grid origin Y (meters, top-left)
        cell_size_m: Cell size in meters

    Returns:
        Affine transform
    """
    return rasterio.Affine(
        cell_size_m, 0.0, origin_x,
        0.0, -cell_size_m, origin_y  # Negative: rows increase downward
    )


def mask_to_geometry(
    mask: np.ndarray,
    origin_x: float,
    origin_y: float,
    cell_size_m: float,
    simplify_tolerance: Optional[float] = None
) -> Polygon | MultiPolygon:
    """Convert binary mask to fire geometry

    Full pipeline:
    1. Connected components
    2. Rasterio polygonization
    3. Geometry repair
    4. Merge into single geometry
    5. Optional simplification

    Args:
        mask: Boolean mask
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters
        simplify_tolerance: Simplification tolerance (meters, optional)

    Returns:
        Polygon or MultiPolygon
    """
    # Create affine transform
    transform = create_affine_transform(origin_x, origin_y, cell_size_m)

    # Polygonize
    polygons = raster_to_polygons(mask, transform)

    if not polygons:
        return MultiPolygon([])

    # Merge into single geometry
    geometry = merge_polygons(polygons)

    # Optional simplification
    if simplify_tolerance is not None and simplify_tolerance > 0:
        geometry = geometry.simplify(simplify_tolerance, preserve_topology=True)
        geometry = repair_geometry(geometry)

    return geometry


def extract_fire_zones(
    arrival_time: np.ndarray,
    current_time: float,
    warning_horizon_minutes: float,
    projection_horizon_minutes: float,
    origin_x: float,
    origin_y: float,
    cell_size_m: float,
    simplify_tolerance: Optional[float] = None
) -> Tuple[Polygon | MultiPolygon, Polygon | MultiPolygon, Polygon | MultiPolygon]:
    """Extract three fire zones from arrival-time field

    Args:
        arrival_time: Arrival time field (minutes)
        current_time: Current simulation time (minutes)
        warning_horizon_minutes: Warning zone horizon
        projection_horizon_minutes: Projection zone horizon
        origin_x: Grid origin X (meters)
        origin_y: Grid origin Y (meters)
        cell_size_m: Cell size in meters
        simplify_tolerance: Simplification tolerance (meters, optional)

    Returns:
        (current_geometry, warning_geometry, projection_geometry)
    """
    # Create zone masks
    current_mask, warning_mask, projection_mask = threshold_arrival_time(
        arrival_time,
        current_time,
        warning_horizon_minutes,
        projection_horizon_minutes
    )

    # Convert masks to geometries
    current_geom = mask_to_geometry(
        current_mask, origin_x, origin_y, cell_size_m, simplify_tolerance
    )
    warning_geom = mask_to_geometry(
        warning_mask, origin_x, origin_y, cell_size_m, simplify_tolerance
    )
    projection_geom = mask_to_geometry(
        projection_mask, origin_x, origin_y, cell_size_m, simplify_tolerance
    )

    return current_geom, warning_geom, projection_geom


def geometry_to_wkt(geom: Polygon | MultiPolygon) -> str:
    """Convert geometry to WKT string

    Args:
        geom: Shapely geometry

    Returns:
        WKT string
    """
    return geom.wkt


def geometry_to_geojson(geom: Polygon | MultiPolygon) -> dict:
    """Convert geometry to GeoJSON dict

    Args:
        geom: Shapely geometry

    Returns:
        GeoJSON dict
    """
    from shapely.geometry import mapping
    return mapping(geom)


def compute_geometry_metrics(geom: Polygon | MultiPolygon) -> dict:
    """Compute geometry metrics

    Args:
        geom: Shapely geometry

    Returns:
        Metrics dict with area_m2, perimeter_m, num_parts
    """
    if geom.is_empty:
        return {
            "area_m2": 0.0,
            "area_hectares": 0.0,
            "perimeter_m": 0.0,
            "num_parts": 0,
        }

    area_m2 = geom.area
    perimeter_m = geom.length

    if isinstance(geom, MultiPolygon):
        num_parts = len(geom.geoms)
    else:
        num_parts = 1

    return {
        "area_m2": float(area_m2),
        "area_hectares": float(area_m2 / 10000.0),
        "perimeter_m": float(perimeter_m),
        "num_parts": int(num_parts),
    }
