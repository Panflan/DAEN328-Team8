CREATE TABLE IF NOT EXISTS etl_state (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_updated TIMESTAMP,
    last_id BIGINT
);