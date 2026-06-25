def matches_filter(event_filter: str, event_type: str) -> bool:
    if event_filter == "*":
        return True
    if event_filter == event_type:
        return True
    if event_filter.endswith(".*"):
        prefix = event_filter[:-2]
        return event_type.startswith(prefix + ".")
    return False
