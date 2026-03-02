def to_int(value, default: int) -> int:
    """Safely convert a value to int with a default fallback."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value, default: float) -> float:
    """Safely convert a value to float with a default fallback."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def slugify_crop(value: str) -> str:
    """Normalize a crop name into a lowercase slug (e.g. 'Tomato' -> 'tomato')."""
    return value.strip().lower().replace(" ", "_").replace("-", "_")

