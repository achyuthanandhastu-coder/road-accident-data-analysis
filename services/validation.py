from datetime import datetime

VALID_SEVERITIES = {"Minor", "Serious", "Fatal", "Unknown"}
MAX_LENGTHS = {"region": 120, "road_name": 180, "vehicle_type": 80, "weather": 80}


def normalize_datetime(value):
    """Accept common HTML and CSV date/time formats and return MySQL DATETIME."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    value = str(value or "").strip()
    formats = (
        "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    raise ValueError("Invalid date/time. Use YYYY-MM-DD HH:MM or YYYY-MM-DDTHH:MM.")


def validate_accident_row(row):
    errors = []
    try:
        normalize_datetime(row.get("accident_datetime"))
    except (ValueError, TypeError):
        errors.append("Enter a valid accident date and time.")

    for field, label in [
        ("region", "Region/location"),
        ("vehicle_type", "Vehicle type"),
        ("severity", "Severity"),
    ]:
        value = row.get(field)
        if value is None or not str(value).strip():
            errors.append(f"{label} is required.")

    for field, max_len in MAX_LENGTHS.items():
        value = row.get(field)
        if value is not None and len(str(value).strip()) > max_len:
            errors.append(f"{field.replace('_', ' ').title()} must be {max_len} characters or fewer.")

    severity = str(row.get("severity", "")).strip().title()
    if severity and severity not in VALID_SEVERITIES:
        errors.append("Severity must be Minor, Serious, Fatal, or Unknown.")

    # Avoid accidental PII in free-text fields. These checks are basic safeguards,
    # not a substitute for reviewing the dataset before importing it.
    for field in ("region", "road_name", "vehicle_type", "weather"):
        value = str(row.get(field) or "")
        if "@" in value:
            errors.append(f"{field.replace('_', ' ').title()} should not contain an email address.")
            break
    return errors
