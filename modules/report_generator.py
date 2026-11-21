"""Generate a Markdown report from the saved experiment log."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from modules.reasoning import is_correct_math_answer
from modules.structured_output import validate_extraction
from modules.zero_few_shot import extract_sentiment

REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "PROMPT_ENGINEERING_REPORT.md"


def _code_block(text: str, language: str = "text") -> str:
    """Fence arbitrary output without changing its contents."""
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{language}\n{text}\n{fence}"


def _format_experiment(record: dict[str, Any]) -> str:
    expected = json.dumps(record.get("expected_output"), ensure_ascii=False)
    lines = [
        f"### Experiment `{record.get('experiment_id', 'unknown')}`",
        f"- **Timestamp (UTC):** {record.get('timestamp', 'unknown')}",
        f"- **Technique:** {record.get('technique', 'unknown')}",
        f"- **Model:** {record.get('model', 'unknown')}",
        f"- **Input:** {record.get('input', '')}",
        f"- **Expected output:** {expected}",
        f"- **Correctness:** {record.get('correctness')}",
        f"- **Validation status:** {record.get('validation_status')}",
        "",
        "**Actual prompt:**",
        _code_block(record.get("prompt", "")),
        "",
    ]
    error = record.get("error", "")
    if error:
        lines.extend(["**API failure (no model output was recorded):**", _code_block(error), ""])
    else:
        lines.extend(
            [
                "**Actual raw model output (preserved as recorded):**",
                _code_block(record.get("raw_model_output", "")),
                "",
            ]
        )
    return "\n".join(lines)


def _section(title: str, records: list[dict[str, Any]]) -> str:
    if not records:
        return f"## {title}\n\n**Not yet run.** No Gemini API experiments for this section have been recorded.\n"
    return f"## {title}\n\n" + "\n".join(_format_experiment(item) for item in records)


def _math_summary(records: list[dict[str, Any]]) -> str:
    if not records:
        return "Not yet run."
    verifiable = [
        item
        for item in records
        if not item.get("error")
        and item.get("expected_output") is not None
        and is_correct_math_answer(
            item.get("raw_model_output", ""), str(item["expected_output"])
        )
        is not None
    ]
    correct = sum(
        is_correct_math_answer(
            item.get("raw_model_output", ""), str(item["expected_output"])
        )
        is True
        for item in verifiable
    )
    unverified = len(records) - len(verifiable)
    accuracy = f"{correct / len(verifiable):.0%}" if verifiable else "N/A"
    return (
        f"{correct}/{len(verifiable)} correct ({accuracy}) among verifiable "
        f"answers; {unverified} of {len(records)} attempts were unverified."
    )


def _sentiment_summary(
    zero_shot: list[dict[str, Any]], few_shot: list[dict[str, Any]]
) -> str:
    def accuracy(records: list[dict[str, Any]]) -> str:
        labeled = [
            item
            for item in records
            if item.get("expected_output") is not None and not item.get("error")
        ]
        checked = [
            item
            for item in labeled
            if extract_sentiment(item.get("raw_model_output", "")) is not None
        ]
        correct = sum(
            extract_sentiment(item.get("raw_model_output", ""))
            == item.get("expected_output")
            for item in checked
        )
        score = f"{correct / len(checked):.0%}" if checked else "N/A"
        return (
            f"{correct}/{len(checked)} correct ({score}) among parseable "
            f"labeled outputs; {len(records) - len(checked)} unverified."
        )

    zero_by_input: dict[str, list[dict[str, Any]]] = defaultdict(list)
    few_by_input: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in zero_shot:
        if item.get("expected_output") is not None:
            zero_by_input[item.get("input", "")].append(item)
    for item in few_shot:
        if item.get("expected_output") is not None:
            few_by_input[item.get("input", "")].append(item)

    pairs = [
        (zero, few)
        for text, zero_items in zero_by_input.items()
        for zero, few in zip(zero_items, few_by_input.get(text, []))
    ]
    comparable = [
        (extract_sentiment(zero.get("raw_model_output", "")),
         extract_sentiment(few.get("raw_model_output", "")))
        for zero, few in pairs
    ]
    comparable = [(zero, few) for zero, few in comparable if zero and few]
    same = sum(zero == few for zero, few in comparable)
    agreement = (
        f"{same}/{len(comparable)} ({same / len(comparable):.0%})"
        if comparable
        else "N/A (no paired parseable outputs)"
    )
    return (
        f"- Zero-shot accuracy: {accuracy(zero_shot)}\n"
        f"- Few-shot accuracy: {accuracy(few_shot)}\n"
        f"- Paired label agreement: {agreement}."
    )


def generate_report(
    experiments: list[dict[str, Any]], report_path: Path = REPORT_PATH
) -> Path:
    """Write a report snapshot using only actual saved records."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    models = sorted({str(item.get("model", "")) for item in experiments if item.get("model")})
    for item in experiments:
        grouped[item.get("technique", "Unknown")].append(item)

    sections = [
        "# Prompt Engineering Mastery Lab — Experiment Report",
        "",
        "> This report is generated from the append-only experiment log. It does "
        "not fabricate or simulate API responses. Sections without saved API "
        "attempts are marked **Not yet run**; failed API calls are included "
        "without being presented as model outputs.",
        "",
        "## 1. Introduction",
        "",
        "This lab compares zero-shot and few-shot sentiment classification, "
        "direct and concise step-by-step mathematical prompting, and Gemini "
        "structured JSON extraction using real API calls.",
        "",
        "## 2. Project objectives",
        "",
        "- Compare sentiment labels with and without five demonstrations.",
        "- Measure math answers against Python-defined expected answers.",
        "- Validate transaction extraction against a JSON schema and Python types.",
        "- Preserve every prompt, API response, result, failure, and timestamp.",
        "",
        "## 3. Model and tools used",
        "",
        f"- **Gemini models represented in the log:** {', '.join(models) if models else 'No API experiments recorded yet.'}",
        "- **SDK:** Google GenAI Python SDK (`google-genai`), using the Gemini Interactions API.",
        "- **Application and analysis:** Python, Streamlit, Pandas, JSON, and python-dotenv.",
        "",
        "## 4. Zero-shot vs Few-shot",
        "",
        "Each recorded entry below contains its actual prompt and raw output. "
        "The benchmark uses five labeled test inputs per mode. Agreement and "
        "format should be interpreted from recorded results; examples may "
        "influence model behavior but do not guarantee better accuracy.",
        "",
        "### Measured results",
        "",
        _sentiment_summary(grouped["Zero-shot"], grouped["Few-shot"]),
        "",
        _section("Zero-shot experiments", grouped["Zero-shot"]),
        "",
        _section("Few-shot experiments", grouped["Few-shot"]),
        "",
        "## 5. Chain-of-Thought",
        "",
        "The step-by-step prompt asks only for a concise explanation of key "
        "calculations, not private internal reasoning. Correctness is checked "
        "by Python against known numerical answers. Accuracy is only meaningful "
        "for attempts with recorded responses; unparseable answers are reported "
        "as unverifiable in the application.",
        "",
        "### Accuracy comparison",
        "",
        f"- Direct prompting: {_math_summary(grouped['Direct math'])}",
        f"- Concise step-by-step prompting: {_math_summary(grouped['Step-by-step math'])}",
        "",
        _section("Direct math experiments", grouped["Direct math"]),
        "",
        _section("Step-by-step math experiments", grouped["Step-by-step math"]),
        "",
        "## 6. Structured Output",
        "",
        "### JSON schema",
        "",
        _code_block(
            json.dumps(
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "date": {"type": "string"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["name", "date", "amount", "currency", "description"],
                },
                indent=2,
            ),
            "json",
        ),
        "",
        "The documented missing-value policy uses empty strings for missing "
        "text fields and `0` for an unstated amount, with the description "
        "clarifying that the amount was not provided. The success rate in the "
        "application counts outputs that parse as JSON and have all required "
        "keys with the required Python types; it is not a measure of semantic accuracy.",
        "",
        "### JSON validation success rate",
        "",
        (
            f"{sum(item.get('validation_status') == 'pass' for item in grouped['Structured output'])}"
            f"/{len(grouped['Structured output'])} attempts "
            f"({sum(item.get('validation_status') == 'pass' for item in grouped['Structured output']) / len(grouped['Structured output']):.0%})"
            if grouped["Structured output"]
            else "**Not yet run.**"
        ),
        "",
        _section("Structured output experiments", grouped["Structured output"]),
        "",
        "## 7. Challenges faced",
        "",
        "API availability depends on a valid local API key, network access, "
        "quota, and model availability. These conditions are recorded as "
        "failures when an attempted request does not complete. JSON parsing "
        "and answer extraction can also fail even when the API call succeeds.",
        "",
        "## 8. What worked and what did not work",
        "",
        "This section is based only on recorded API attempts. No result is "
        "described as successful unless it appears in the experiment log. "
        "See the measured sentiment, math, and JSON summaries above; review "
        "individual successful and failed entries in the experiment details.",
        "",
        "## 9. Conclusion",
        "",
        "Run the benchmark buttons in the application to add real Gemini "
        "responses, then regenerate this report. Conclusions should be drawn "
        "from those recorded experiments rather than assumed in advance.",
        "",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(sections), encoding="utf-8")
    return report_path
