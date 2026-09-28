-- Add SOS requests table
-- Migration: Add sos_requests table for citizen emergency requests

CREATE TABLE IF NOT EXISTS sos_requests (
    sos_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
    location GEOGRAPHY(Point, 4326),
    location_lat DOUBLE PRECISION,
    location_lon DOUBLE PRECISION,
    message TEXT,
    device_info VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_sos_requests_status ON sos_requests(status);
CREATE INDEX IF NOT EXISTS idx_sos_requests_created_at ON sos_requests(created_at DESC);

COMMENT ON TABLE sos_requests IS 'Citizen emergency SOS requests';
COMMENT ON COLUMN sos_requests.sos_id IS 'Unique SOS request identifier';
COMMENT ON COLUMN sos_requests.status IS 'QUEUED, SENT, ACKNOWLEDGED, UNREACHABLE, RESOLVED';
COMMENT ON COLUMN sos_requests.location IS 'Citizen location at time of SOS';
