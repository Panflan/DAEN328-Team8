from load import clean_text, make_location_key


def test_clean_text_replaces_blank_values():
    assert clean_text("   ", "Unknown") == "Unknown"


def test_location_key_is_readable_and_stable():
    record = {"borough": "BROOKLYN", "incident_zip": "11201"}

    assert make_location_key(record) == "BROOKLYN|11201||"
