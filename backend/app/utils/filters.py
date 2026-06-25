"""Helpers for building SQL filter conditions from comma-separated query params."""


def multi_value_condition(column: str, prefix: str, csv_value: str, params: dict) -> str:
    """Build = or IN condition for a potentially comma-separated value."""
    vals = [v.strip() for v in csv_value.split(",") if v.strip()]
    if len(vals) == 1:
        params[prefix] = vals[0]
        return f"{column} = :{prefix}"
    for i, v in enumerate(vals):
        params[f"{prefix}_{i}"] = v
    placeholders = ", ".join(f":{prefix}_{i}" for i in range(len(vals)))
    return f"{column} IN ({placeholders})"


def multi_value_int_condition(column: str, prefix: str, csv_value: str, params: dict) -> str:
    """Build = or IN condition for comma-separated integer values."""
    vals = [v.strip() for v in csv_value.split(",") if v.strip()]
    if len(vals) == 1:
        params[prefix] = int(vals[0])
        return f"{column} = :{prefix}"
    for i, v in enumerate(vals):
        params[f"{prefix}_{i}"] = int(v)
    placeholders = ", ".join(f":{prefix}_{i}" for i in range(len(vals)))
    return f"{column} IN ({placeholders})"
