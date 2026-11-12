-- PostgreSQL schema for the NYC 311 ETL pipeline.
-- Dimension tables hold facts that repeat across many service requests.

CREATE TABLE IF NOT EXISTS etl_state (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_updated TIMESTAMPTZ NOT NULL,
    last_id BIGINT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complaint_types (
    complaint_type_id BIGSERIAL PRIMARY KEY,
    complaint_type VARCHAR(255) NOT NULL,
    descriptor VARCHAR(255) NOT NULL DEFAULT 'Unknown',
    CONSTRAINT complaint_types_natural_key UNIQUE (complaint_type, descriptor)
);

CREATE TABLE IF NOT EXISTS agencies (
    agency_id BIGSERIAL PRIMARY KEY,
    agency_code VARCHAR(20) NOT NULL UNIQUE,
    agency_name VARCHAR(255) NOT NULL DEFAULT 'Unknown'
);

CREATE TABLE IF NOT EXISTS locations (
    location_id BIGSERIAL PRIMARY KEY,
    location_key TEXT NOT NULL UNIQUE,
    borough VARCHAR(50) NOT NULL DEFAULT 'Unknown',
    incident_zip VARCHAR(10),
    community_board VARCHAR(100),
    city VARCHAR(100),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7)
);

CREATE TABLE IF NOT EXISTS service_requests (
    unique_key BIGINT PRIMARY KEY,
    complaint_type_id BIGINT NOT NULL REFERENCES complaint_types(complaint_type_id),
    agency_id BIGINT NOT NULL REFERENCES agencies(agency_id),
    location_id BIGINT REFERENCES locations(location_id),
    created_date TIMESTAMPTZ NOT NULL,
    closed_date TIMESTAMPTZ,
    status VARCHAR(50),
    resolution_description TEXT,
    incident_address VARCHAR(255),
    location_type VARCHAR(100),
    source_updated_at TIMESTAMPTZ NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_requests_created_date
    ON service_requests (created_date);

CREATE INDEX IF NOT EXISTS idx_service_requests_status
    ON service_requests (status);
