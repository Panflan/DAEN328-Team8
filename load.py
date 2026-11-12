"""Load NYC 311 records into PostgreSQL."""


def clean_text(value, default=None):
    """Turn blank values into a useful default."""
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def to_float(value):
    """Convert latitude and longitude when they are present."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_location_key(record):
    """Build a readable location key from fields that describe one location."""
    borough = clean_text(record.get("borough"), "Unknown")
    zip_code = clean_text(record.get("incident_zip"), "")
    community_board = clean_text(record.get("community_board"), "")
    city = clean_text(record.get("city"), "")
    return f"{borough}|{zip_code}|{community_board}|{city}"


def load_records(records, connection):
    """Insert new records and update records that are already in the database."""
    stats = {
        "received": 0,
        "skipped": 0,
        "duplicate_input_rows": 0,
        "inserted": 0,
        "updated": 0,
    }
    seen_keys = set()

    try:
        with connection.cursor() as cursor:
            for record in records:
                stats["received"] += 1

                try:
                    unique_key = int(record["unique_key"])
                except (KeyError, TypeError, ValueError):
                    stats["skipped"] += 1
                    continue

                if unique_key in seen_keys:
                    stats["duplicate_input_rows"] += 1
                    continue
                seen_keys.add(unique_key)

                created_date = record.get("created_date")
                source_updated_at = record.get(":updated_at")
                if not created_date or not source_updated_at:
                    stats["skipped"] += 1
                    continue

                # Insert or find the complaint type.
                complaint_type = clean_text(record.get("complaint_type"), "Unknown")
                descriptor = clean_text(record.get("descriptor"), "Unknown")
                cursor.execute(
                    """
                    INSERT INTO complaint_types (complaint_type, descriptor)
                    VALUES (%s, %s)
                    ON CONFLICT (complaint_type, descriptor) DO UPDATE
                        SET complaint_type = EXCLUDED.complaint_type
                    RETURNING complaint_type_id;
                    """,
                    (complaint_type, descriptor),
                )
                complaint_type_id = cursor.fetchone()[0]

                # Insert or find the agency.
                agency_code = clean_text(record.get("agency"), "Unknown")
                agency_name = clean_text(record.get("agency_name"), "Unknown")
                cursor.execute(
                    """
                    INSERT INTO agencies (agency_code, agency_name)
                    VALUES (%s, %s)
                    ON CONFLICT (agency_code) DO UPDATE
                        SET agency_name = EXCLUDED.agency_name
                    RETURNING agency_id;
                    """,
                    (agency_code, agency_name),
                )
                agency_id = cursor.fetchone()[0]

                # Insert or find the location.
                location_key = make_location_key(record)
                cursor.execute(
                    """
                    INSERT INTO locations (
                        location_key, borough, incident_zip, community_board,
                        city, latitude, longitude
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_key) DO UPDATE
                        SET borough = EXCLUDED.borough,
                            incident_zip = EXCLUDED.incident_zip,
                            community_board = EXCLUDED.community_board,
                            city = EXCLUDED.city,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude
                    RETURNING location_id;
                    """,
                    (
                        location_key,
                        clean_text(record.get("borough"), "Unknown"),
                        clean_text(record.get("incident_zip")),
                        clean_text(record.get("community_board")),
                        clean_text(record.get("city")),
                        to_float(record.get("latitude")),
                        to_float(record.get("longitude")),
                    ),
                )
                location_id = cursor.fetchone()[0]

                # Check whether this request already exists so the summary is easy to read.
                cursor.execute(
                    "SELECT 1 FROM service_requests WHERE unique_key = %s;",
                    (unique_key,),
                )
                already_exists = cursor.fetchone() is not None

                cursor.execute(
                    """
                    INSERT INTO service_requests (
                        unique_key, complaint_type_id, agency_id, location_id,
                        created_date, closed_date, status, resolution_description,
                        incident_address, location_type, source_updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (unique_key) DO UPDATE
                        SET complaint_type_id = EXCLUDED.complaint_type_id,
                            agency_id = EXCLUDED.agency_id,
                            location_id = EXCLUDED.location_id,
                            created_date = EXCLUDED.created_date,
                            closed_date = EXCLUDED.closed_date,
                            status = EXCLUDED.status,
                            resolution_description = EXCLUDED.resolution_description,
                            incident_address = EXCLUDED.incident_address,
                            location_type = EXCLUDED.location_type,
                            source_updated_at = EXCLUDED.source_updated_at,
                            loaded_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        unique_key,
                        complaint_type_id,
                        agency_id,
                        location_id,
                        created_date,
                        record.get("closed_date"),
                        clean_text(record.get("status")),
                        clean_text(record.get("resolution_description")),
                        clean_text(record.get("incident_address")),
                        clean_text(record.get("location_type")),
                        source_updated_at,
                    ),
                )

                if already_exists:
                    stats["updated"] += 1
                else:
                    stats["inserted"] += 1

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return stats
