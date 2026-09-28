import re

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_b2.py", "r") as f:
    content = f.read()

# Make sure imports are present
if "from shapely.geometry import mapping" not in content:
    content = content.replace("from pydantic import BaseModel, Field", "from pydantic import BaseModel, Field\nfrom geoalchemy2.shape import to_shape\nfrom shapely.geometry import mapping\nfrom db.models_c import FireGeometry")

# Update IncidentResponse model to include geometry_geojson
if "geometry_geojson: Optional[dict] = None" not in content:
    content = content.replace("centroid: Optional[dict] = None  # {lat, lon}", "centroid: Optional[dict] = None  # {lat, lon}\n    geometry_geojson: Optional[dict] = None")

# Update _incident_to_response to map the geometry
mapper = """created_at=incident.created_at,
        updated_at=incident.updated_at,
        centroid={"lat": incident.centroid_lat, "lon": incident.centroid_lon} if incident.centroid_lat else None,"""
mapper_replacement = """created_at=incident.created_at,
        updated_at=incident.updated_at,
        centroid={"lat": incident.centroid_lat, "lon": incident.centroid_lon} if incident.centroid_lat else None,
        geometry_geojson=mapping(to_shape(incident.geometry)) if incident.geometry is not None else None,"""
content = content.replace(mapper, mapper_replacement)

# Add the GET /incidents/{id}/geometries endpoint
geometry_endpoint = """
@router_b2.get("/incidents/{incident_id}/geometries")
async def get_incident_geometries(
    incident_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    \"\"\"
    Get all active geometry zones (CURRENT, WARNING, PROJECTION) for an incident as a GeoJSON FeatureCollection.
    \"\"\"
    try:
        # Verify incident exists
        try:
            incident_uuid = uuid.UUID(incident_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid incident ID format: {incident_id}")

        incident = await session.get(Incident, incident_uuid)
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident not found: {incident_id}")

        # Query all geometries for this incident from FireGeometry table
        result = await session.execute(
            select(FireGeometry)
            .where(FireGeometry.incident_id == incident_uuid)
            .order_by(desc(FireGeometry.generated_at))
        )
        geometries = result.scalars().all()
        
        # Deduplicate by zone_type (take latest only)
        latest_geos = {}
        for geo in geometries:
            if geo.zone_type not in latest_geos:
                latest_geos[geo.zone_type] = geo

        features = []
        for zone_type, geo in latest_geos.items():
            if geo.geometry is not None:
                shape = to_shape(geo.geometry)
                features.append({
                    "type": "Feature",
                    "properties": {
                        "zone_type": zone_type,
                        "generated_at": geo.generated_at.isoformat(),
                        "area_hectares": geo.area_hectares
                    },
                    "geometry": mapping(shape)
                })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident geometries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
"""

if "get_incident_geometries" not in content:
    content += geometry_endpoint

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_b2.py", "w") as f:
    f.write(content)

