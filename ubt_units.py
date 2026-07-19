UBT_UNITS = [
    "601-1",
    "601-2",
    "602-1",
    "602-2",
    "602-3",
    "604-1",
    "604-2",
    "604-3",
    "605-1",
    "605-2",
    "606-1",
    "607-1",
    "607-2",
    "607-3",
    "608-1",
    "608-2",
    "608-3",
    "609-1",
    "609-2",
    "609-3",
    "609-4",
    "610-1",
    "611-1",
    "611-2",
    "611-3",
    "612-1",
    "612-2",
    "612-3",
]

UBT_UNITS_SET = set(UBT_UNITS)


def is_valid_ubt(ubt: str) -> bool:
    return ubt in UBT_UNITS_SET


def normalize_ubt(value: str) -> str | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    if cleaned in UBT_UNITS_SET:
        return cleaned
    return None
