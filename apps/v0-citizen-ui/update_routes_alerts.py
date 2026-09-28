import re

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_alerts.py", "r") as f:
    content = f.read()

# Make sure shapely Geometry and from_shape are imported
if "from shapely.geometry import Point" not in content:
    content = content.replace("from sqlalchemy import select, desc, and_", "from sqlalchemy import select, desc, and_\nfrom shapely.geometry import Point\nfrom geoalchemy2.shape import from_shape")


incident_creation = """test_incident = Incident(
            incident_id=uuid.uuid4(),
            state="ACTIVE",
            information_condition="GOOD",
            first_observed_at=datetime.now(timezone.utc),
            last_observed_at=datetime.now(timezone.utc),
            created_by="test_endpoint",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            centroid_lat=13.13495,
            centroid_lon=77.56681,
            geometry=from_shape(Point(77.56681, 13.13495), srid=4326)
        )"""

content = re.sub(
    r'test_incident = Incident\(\s*incident_id=uuid\.uuid4\(\),\s*state="ACTIVE",\s*information_condition="GOOD",\s*first_observed_at=datetime\.now\(timezone\.utc\),\s*last_observed_at=datetime\.now\(timezone\.utc\),\s*created_by="test_endpoint",\s*created_at=datetime\.now\(timezone\.utc\),\s*updated_at=datetime\.now\(timezone\.utc\)\s*\)',
    incident_creation,
    content
)

with open("/home/ericsri/nexalert-sih/services/backend/modules/api/routes_alerts.py", "w") as f:
    f.write(content)

