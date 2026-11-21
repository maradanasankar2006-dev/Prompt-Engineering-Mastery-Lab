"""Schema, test inputs, and validation for transaction extraction."""

import json

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "date": {"type": "string"},
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "description": {"type": "string"},
    },
    "required": ["name", "date", "amount", "currency", "description"],
}

TEST_INPUTS = [
    {
        "name": "Normal payment",
        "input": (
            "Maya paid USD 48.50 to Northstar Books on 2026-03-15 "
            "for workshop supplies."
        ),
    },
    {
        "name": "Messy invoice",
        "input": (
            "INV# 8831 | BILLED TO: Omar Chen | 14/07/2026 | "
            "consulting retainer. TOTAL DUE EUR 1,240.00. Thanks!"
        ),
    },
    {
        "name": "Missing amount",
        "input": (
            "Nina paid for a taxi on March 2, 2026. The receipt amount "
            "was not recorded."
        ),
    },
    {
        "name": "Different date format",
        "input": (
            "On 21 Nov 2026, Riku paid JPY 12000 for replacement parts."
        ),
    },
    {
        "name": "Different currency",
        "input": (
            "A CAD 73.25 subscription charge was made by Elena on "
            "2026/10/09 for the design service."
        ),
    },
]


def build_extraction_prompt(text: str) -> str:
    """Build an extraction prompt with the schema and missing-value policy."""
    schema_text = json.dumps(JSON_SCHEMA, indent=2)
    return (
        "Extract the transaction information from the supplied text. Return "
        "only a JSON object matching this JSON Schema exactly:\n"
        f"{schema_text}\n\n"
        "Missing-value policy: use an empty string for a missing name, date, "
        "currency, or description. Because amount must be a number, use 0 when "
        "the amount is not stated, and say that the amount was not provided in "
        "description. Preserve the date as written when it is present. Do not "
        "guess facts.\n\n"
        f"Text to extract:\n{text}"
    )


def validate_extraction(output: str) -> tuple[bool, str, dict | None]:
    """Parse JSON and check that all fields have the required JSON types."""
    try:
        value = json.loads(output, parse_constant=_reject_nonstandard_constant)
    except (json.JSONDecodeError, ValueError) as error:
        return False, f"Invalid JSON: {error}", None

    if not isinstance(value, dict):
        return False, "The JSON root must be an object.", None

    expected_keys = set(JSON_SCHEMA["properties"])
    actual_keys = set(value)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        return False, "; ".join(details), value

    for key in ("name", "date", "currency", "description"):
        if not isinstance(value[key], str):
            return False, f"'{key}' must be a string.", value
    if isinstance(value["amount"], bool) or not isinstance(
        value["amount"], (int, float)
    ):
        return False, "'amount' must be a number (not a boolean).", value

    return True, "Valid JSON with all required keys and types.", value


def _reject_nonstandard_constant(value: str) -> None:
    """Reject NaN and Infinity, which Python accepts but JSON does not."""
    raise ValueError(f"{value} is not a valid JSON number.")
