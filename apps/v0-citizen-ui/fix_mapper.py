import re

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_b2.py", "r") as f:
    content = f.read()

mapper_old = """    return IncidentResponse(
        incident_id=str(incident.incident_id),
        state=incident.state,
        information_condition=incident.information_condition,
        centroid=centroid,
        hazard_assessments=[
            _incident_hazard_to_response(h) 
            for h in (incident.hazard_assessments if hasattr(incident, 'hazard_assessments') else [])
        ],
        source_summary=incident.source_summary,
        first_observed_at=incident.first_observed_at,
        last_observed_at=incident.last_observed_at,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at
    )"""

mapper_new = """    return IncidentResponse(
        incident_id=str(incident.incident_id),
        state=incident.state,
        information_condition=incident.information_condition,
        centroid=centroid,
        geometry_geojson=mapping(to_shape(incident.geometry)) if hasattr(incident, 'geometry') and incident.geometry is not None else None,
        hazard_assessments=[
            _incident_hazard_to_response(h) 
            for h in (incident.hazard_assessments if hasattr(incident, 'hazard_assessments') else [])
        ],
        source_summary=incident.source_summary,
        first_observed_at=incident.first_observed_at,
        last_observed_at=incident.last_observed_at,
        resolved_at=incident.resolved_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at
    )"""

if "geometry_geojson=mapping" not in content:
    content = content.replace(mapper_old, mapper_new)

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_b2.py", "w") as f:
    f.write(content)

