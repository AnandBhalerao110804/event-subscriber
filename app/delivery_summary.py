IN_PROGRESS_STATUSES = frozenset({"pending", "delivering", "failed"})


def summarize_delivery_statuses(statuses: list[str]) -> str:
    if not statuses:
        return "no_deliveries"
    if all(status == "delivered" for status in statuses):
        return "delivered"
    if all(status == "dead" for status in statuses):
        return "dead"
    if all(status == "pending" for status in statuses):
        return "pending"
    if any(status in IN_PROGRESS_STATUSES for status in statuses):
        return "in_progress"
    return "partial"
