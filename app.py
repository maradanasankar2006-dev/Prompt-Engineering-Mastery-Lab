"""Interactive demonstrations of three prompt engineering techniques."""

import os
import re
from typing import Any, Callable

import pandas as pd
import streamlit as st
import httpx2
from google.genai.errors import APIError

from modules.experiment_tracker import load_experiments, record_experiment
from modules.gemini_client import generate_text, get_model_name
from modules.reasoning import (
    MATH_PROBLEMS,
    build_direct_prompt,
    build_step_by_step_prompt,
    is_correct_math_answer,
)
from modules.report_generator import generate_report
from modules.structured_output import (
    JSON_SCHEMA,
    TEST_INPUTS,
    build_extraction_prompt,
    validate_extraction,
)
from modules.zero_few_shot import (
    TEST_SENTENCES,
    build_few_shot_prompt,
    build_zero_shot_prompt,
    extract_sentiment,
)

st.set_page_config(
    page_title="Prompt Engineering Mastery Lab",
    page_icon=":material/science:",
    layout="wide",
)

PAGES = [
    "Dashboard",
    "Zero-shot vs Few-shot",
    "Chain-of-Thought",
    "Structured Output",
    "Results & Analysis",
]

Validator = Callable[[str], tuple[bool | None, str]]


def _check_sentiment(
    output: str, expected: str | None
) -> tuple[bool | None, str]:
    if expected is None:
        return None, "not_applicable"
    actual = extract_sentiment(output)
    if actual is None:
        return None, "unverifiable"
    return actual == expected, "pass" if actual == expected else "fail"


def _check_math(output: str, expected: str) -> tuple[bool | None, str]:
    correct = is_correct_math_answer(output, expected)
    if correct is None:
        return None, "unverifiable"
    return correct, "pass" if correct else "fail"


def _safe_error_message(error: Exception) -> str:
    """Avoid accidentally displaying a configured key in an error message."""
    message = str(error)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    message = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", message)
    return f"{type(error).__name__}: {message}"


def run_logged_call(
    technique: str,
    input_text: str,
    prompt: str,
    *,
    expected_output: Any = None,
    response_schema: dict | None = None,
    validator: Validator | None = None,
) -> dict[str, Any]:
    """Call Gemini and append both successful responses and request failures."""
    try:
        output = generate_text(prompt, response_schema=response_schema)
    except (APIError, httpx2.HTTPError, TimeoutError, OSError, ValueError) as error:
        message = _safe_error_message(error)
        return record_experiment(
            technique=technique,
            input_text=input_text,
            prompt=prompt,
            expected_output=expected_output,
            validation_status="api_error",
            model=get_model_name(),
            error=message,
        )

    correctness = None
    validation_status = "not_applicable"
    if validator is not None:
        correctness, validation_status = validator(output)
    return record_experiment(
        technique=technique,
        input_text=input_text,
        prompt=prompt,
        raw_model_output=output,
        expected_output=expected_output,
        correctness=correctness,
        validation_status=validation_status,
        model=get_model_name(),
    )


def _render_record(record: dict[str, Any]) -> None:
    """Show an actual experiment result and its exact prompt."""
    if record.get("error"):
        st.error(f"API request failed: {record['error']}")
    else:
        st.markdown("**Actual Gemini response**")
        st.code(record.get("raw_model_output", ""), language="text")
    with st.expander("Show exact prompt used"):
        st.code(record.get("prompt", ""), language="text")
    if record.get("validation_status") not in ("not_applicable", "api_error"):
        status = record["validation_status"]
        if status == "pass":
            st.success("Validation: passed")
        elif status == "fail":
            st.warning("Validation: failed")
        else:
            st.info(f"Validation: {status}")
        if record.get("correctness") is not None:
            st.write(f"Correct answer: **{record['correctness']}**")


def _render_dashboard() -> None:
    st.title("Prompt Engineering Mastery Lab")
    st.markdown(
        "A hands-on lab for seeing how prompt structure changes real Gemini "
        "outputs—not a general-purpose chatbot."
    )

    cards = st.columns(3)
    cards[0].markdown(
    card_content = [
        (
            "Zero-shot vs few-shot",
            ":material/target:",
            "Classify sentiment with no demonstrations, then with five labeled "
            "examples. Compare raw outputs and labels.",
        ),
        (
            "Chain-of-Thought",
            ":material/calculate:",
            "Compare direct math answers with concise key calculation steps. "
            "Python checks both against known answers.",
        ),
        (
            "Structured output",
            ":material/data_object:",
            "Extract transaction fields from messy text using Gemini JSON mode "
            "and validate the returned JSON with Python.",
        ),
    ]
    for column, (title, icon, description) in zip(cards, card_content):
        with column:
            with st.container(border=True, height="stretch"):
                st.subheader(title, icon=icon)
                st.write(description)

    st.subheader("Project objectives")
    st.markdown(
        "- Run controlled, comparable prompts against the same Gemini model.\n"
        "- Inspect the exact prompt and unmodified model response.\n"
        "- Measure accuracy or JSON validity instead of assuming success.\n"
        "- Keep an append-only experiment log and generate a report from it."
    )
    st.subheader("Technology stack")
    st.write(
        "Python · Streamlit · Google GenAI SDK (Gemini) · JSON · Pandas · "
        "python-dotenv"
    )
    st.caption(f"Configured model: `{get_model_name()}`")

    if not os.getenv("GEMINI_API_KEY", "").strip():
        st.info(
            "Setup needed: add your Gemini API key to `.env`. The key is never "
            "shown in this app."
        )


def _render_zero_few() -> None:
    st.title("Zero-shot vs Few-shot Prompting")
    st.write(
        "Both approaches classify the same text. Zero-shot provides instructions "
        "only; few-shot adds five labeled demonstrations."
    )
    text = st.text_area(
        "Enter a sentence or review",
        value="The product works well and arrived on time.",
        height=100,
    )
    run_one = st.button("Run comparison", type="primary", key="sentiment_one")
    run_benchmark = st.button("Run all 5 test sentences", key="sentiment_benchmark")

    if run_one or run_benchmark:
        cases = [{"input": text, "expected": None}] if run_one else TEST_SENTENCES
        results = []
        progress = st.progress(0)
        for index, case in enumerate(cases):
            for technique, prompt_builder in (
                ("Zero-shot", build_zero_shot_prompt),
                ("Few-shot", build_few_shot_prompt),
            ):
                prompt = prompt_builder(case["input"])
                results.append(
                    run_logged_call(
                        technique,
                        case["input"],
                        prompt,
                        expected_output=case["expected"],
                        validator=lambda output, expected=case["expected"]: _check_sentiment(
                            output, expected
                        ),
                    )
                )
            progress.progress((index + 1) / len(cases))
        st.session_state["sentiment_results"] = results

    results = st.session_state.get("sentiment_results", [])
    for index in range(0, len(results), 2):
        zero, few = results[index : index + 2]
        st.subheader(f"Input: {zero['input']}")
        left, right = st.columns(2)
        with left:
            st.markdown("**Zero-shot**")
            _render_record(zero)
        with right:
            st.markdown("**Few-shot**")
            _render_record(few)
        zero_label = extract_sentiment(zero.get("raw_model_output", ""))
        few_label = extract_sentiment(few.get("raw_model_output", ""))
        if zero_label and few_label:
            st.caption(
                f"Parsed labels: {zero_label} / {few_label} — "
                f"{'same label' if zero_label == few_label else 'different labels'}."
            )
    st.info(
        "Few-shot examples demonstrate the desired labels and response format. "
        "They can influence model behavior, but they do not guarantee more "
        "accurate or consistent classifications."
    )


def _render_math() -> None:
    st.title("Chain-of-Thought Prompting")
    st.write(
        "Compare a direct answer with a prompt asking for a concise explanation "
        "of key calculation steps. No private internal reasoning is requested."
    )
    problem_names = [problem.name for problem in MATH_PROBLEMS]
    selected_name = st.selectbox("Choose a word problem", problem_names)
    problem = next(item for item in MATH_PROBLEMS if item.name == selected_name)
    st.markdown(f"**Problem:** {problem.question}")
    st.caption("Expected numerical answer is checked locally with Python.")
    if st.button("Run both prompts", type="primary", key="math_one"):
        records = []
        for technique, builder in (
            ("Direct math", build_direct_prompt),
            ("Step-by-step math", build_step_by_step_prompt),
        ):
            prompt = builder(problem.question)
            records.append(
                run_logged_call(
                    technique,
                    problem.question,
                    prompt,
                    expected_output=problem.expected_answer,
                    validator=lambda output, expected=problem.expected_answer: _check_math(
                        output, expected
                    ),
                )
            )
        st.session_state["math_results"] = records

    if st.button("Run all 5 math problems", key="math_benchmark"):
        records = []
        progress = st.progress(0)
        for index, item in enumerate(MATH_PROBLEMS):
            for technique, builder in (
                ("Direct math", build_direct_prompt),
                ("Step-by-step math", build_step_by_step_prompt),
            ):
                records.append(
                    run_logged_call(
                        technique,
                        item.question,
                        builder(item.question),
                        expected_output=item.expected_answer,
                        validator=lambda output, expected=item.expected_answer: _check_math(
                            output, expected
                        ),
                    )
                )
            progress.progress((index + 1) / len(MATH_PROBLEMS))
        st.session_state["math_results"] = records

    results = st.session_state.get("math_results", [])
    for index in range(0, len(results), 2):
        direct, stepwise = results[index : index + 2]
        st.subheader(direct["input"])
        left, right = st.columns(2)
        with left:
            st.markdown("**Direct prompt**")
            _render_record(direct)
        with right:
            st.markdown("**Concise step-by-step prompt**")
            _render_record(stepwise)
        st.caption(
            f"Expected: {direct.get('expected_output')}; "
            f"direct: {direct.get('correctness')}; "
            f"step-by-step: {stepwise.get('correctness')}."
        )


def _render_structured_output() -> None:
    st.title("Structured Output (JSON)")
    st.write(
        "Extract five transaction fields from messy text. Gemini is asked to "
        "follow an explicit JSON schema and uses its JSON response mode."
    )
    with st.expander("View JSON schema and missing-value policy"):
        st.json(JSON_SCHEMA)
        st.write(
            "Missing text fields use an empty string. A missing amount uses 0 "
            "and the description must state that the amount was not provided."
        )
    text = st.text_area(
        "Paste payment, invoice, or expense text",
        value=TEST_INPUTS[0]["input"],
        height=120,
    )
    run_one = st.button("Extract fields", type="primary", key="json_one")
    run_tests = st.button("Run all 5 test inputs", key="json_benchmark")

    if run_one or run_tests:
        cases = (
            [{"name": "Custom input", "input": text}]
            if run_one
            else TEST_INPUTS
        )
        records = []
        progress = st.progress(0)
        for index, case in enumerate(cases):
            prompt = build_extraction_prompt(case["input"])

            def validate(output: str) -> tuple[bool | None, str]:
                valid, message, _ = validate_extraction(output)
                return valid, "pass" if valid else f"fail: {message}"

            records.append(
                run_logged_call(
                    "Structured output",
                    case["input"],
                    prompt,
                    expected_output=None,
                    response_schema=JSON_SCHEMA,
                    validator=validate,
                )
            )
            records[-1]["case_name"] = case["name"]
            progress.progress((index + 1) / len(cases))
        st.session_state["structured_results"] = records

    for record in st.session_state.get("structured_results", []):
        st.subheader(record.get("case_name", "Extraction result"))
        st.write(f"**Input:** {record['input']}")
        if record.get("error"):
            _render_record(record)
            continue
        valid, message, parsed = validate_extraction(record["raw_model_output"])
        if valid:
            st.success(message)
            st.json(parsed)
        else:
            st.error(message)
            st.code(record["raw_model_output"], language="text")
        with st.expander("Show exact prompt and raw response"):
            st.markdown("**Prompt**")
            st.code(record["prompt"], language="text")
            st.markdown("**Raw response**")
            st.code(record["raw_model_output"], language="text")
    st.caption(
        "JSON success rate means valid JSON with exactly the required field "
        "names and Python types. It does not confirm that extracted facts are "
        "semantically correct."
    )


def _render_results() -> None:
    st.title("Results & Analysis")
    experiments = load_experiments()
    if not experiments:
        st.info("No experiments are recorded yet. Run one of the technique pages.")
    else:
        frame = pd.DataFrame(experiments)
        st.metric("Recorded API attempts", len(frame))
        if "technique" in frame:
            st.dataframe(
                frame[
                    [
                        column
                        for column in (
                            "timestamp",
                            "technique",
                            "model",
                            "correctness",
                            "validation_status",
                            "error",
                        )
                        if column in frame
                    ]
                ],
                hide_index=True,
                alt="Saved prompt experiment results",
            )

        math_records = frame[frame["technique"].isin(["Direct math", "Step-by-step math"])]
        if not math_records.empty:
            st.subheader("Math answer accuracy")
            for technique in ("Direct math", "Step-by-step math"):
                selected = math_records[math_records["technique"] == technique]
                valid_answers = selected[selected["correctness"].notna()]
                accuracy = (
                    float(valid_answers["correctness"].astype(bool).mean())
                    if not valid_answers.empty
                    else None
                )
                st.metric(
                    technique,
                    f"{accuracy:.0%}" if accuracy is not None else "No verifiable answers",
                    help=(
                        f"{int(valid_answers['correctness'].astype(bool).sum())} "
                        f"correct / {len(valid_answers)} parseable outputs; "
                        f"{len(selected) - len(valid_answers)} unverified."
                    ),
                )

        json_records = frame[frame["technique"] == "Structured output"]
        if not json_records.empty:
            success = json_records["validation_status"].eq("pass").sum()
            st.subheader("Structured JSON validity")
            st.metric(
                "Success rate",
                f"{success / len(json_records):.0%}",
                help=f"{success} valid outputs / {len(json_records)} total API attempts.",
            )

        sentiment_records = frame[frame["technique"].isin(["Zero-shot", "Few-shot"])]
        if not sentiment_records.empty:
            st.subheader("Sentiment benchmark accuracy")
            for technique in ("Zero-shot", "Few-shot"):
                selected = sentiment_records[sentiment_records["technique"] == technique]
                expected = selected[selected["expected_output"].notna()]
                checked = expected[expected["correctness"].notna()]
                accuracy = (
                    float(checked["correctness"].astype(bool).mean())
                    if not checked.empty
                    else None
                )
                st.metric(
                    technique,
                    f"{accuracy:.0%}" if accuracy is not None else "No benchmark results",
                    help=f"{len(checked)} of {len(expected)} labeled outputs could be checked.",
                )

    st.subheader("Generate the written report")
    st.write(
        "The Markdown report is built from the saved log. It preserves actual "
        "prompts and raw outputs, includes failures, and labels unrun sections."
    )
    if st.button("Generate PROMPT_ENGINEERING_REPORT.md", type="primary"):
        report_path = generate_report(experiments)
        st.success(f"Report generated: `{report_path}`")
        st.download_button(
            "Download report",
            data=report_path.read_text(encoding="utf-8"),
            file_name=report_path.name,
            mime="text/markdown",
        )


def main() -> None:
    with st.sidebar:
        st.title("Prompt lab", icon=":material/science:")
        page = st.radio("Pages", PAGES)
        st.caption(f"Model: `{get_model_name()}`")

    pages = {
        "Dashboard": _render_dashboard,
        "Zero-shot vs Few-shot": _render_zero_few,
        "Chain-of-Thought": _render_math,
        "Structured Output": _render_structured_output,
        "Results & Analysis": _render_results,
    }
    pages[page]()


if __name__ == "__main__":
    main()
