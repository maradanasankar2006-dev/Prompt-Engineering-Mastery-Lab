# Prompt Engineering Mastery Lab — Experiment Report

> This initial report snapshot contains no Gemini API experiment results. Nothing has been simulated or fabricated. Each experiment section is marked **Not yet run** until a real API attempt is saved in `data/experiments.json`.

## 1. Introduction

This lab compares zero-shot and few-shot sentiment classification, direct and concise step-by-step mathematical prompting, and Gemini structured JSON extraction using real API calls.

## 2. Project objectives

- Compare sentiment classification with and without five labeled examples.
- Compare direct and concise step-by-step math answers against Python-checked answers.
- Validate extracted transaction information as JSON with the required fields and types.
- Keep prompts, actual outputs, failures, and timestamps for reproducibility.

## 3. Model and tools used

- **Gemini model:** `gemini-4-hydrogen` by default; configurable with `GEMINI_MODEL`.
- **API SDK:** Google GenAI Python SDK (`google-genai`) and its Gemini Interactions API.
- **Application and analysis:** Python, Streamlit, Pandas, JSON, and python-dotenv.
- No API calls have been made for this initial report.

## 4. Zero-shot vs Few-shot

No zero-shot or few-shot API experiments have been run yet. The app provides five sentiment test sentences and records both the exact prompt and raw output for each mode.

## 5. Chain-of-Thought

No math API experiments have been run yet. The app includes five multi-step word problems and checks parsed numerical responses against Python-defined answers. Step-by-step prompts request concise key calculations, not private internal reasoning.

## 6. Structured Output

### JSON schema

```json
{
  "name": "string",
  "date": "string",
  "amount": "number",
  "currency": "string",
  "description": "string"
}
```

No structured output API experiments have been run yet. The app provides five test inputs, including a missing amount, messy invoice text, multiple date formats, and different currencies. Validity is measured by JSON parsing and required field types; semantic extraction accuracy is not inferred from schema validity.

## 7. Challenges faced

The Gemini API key, network availability, model availability, and quota are required to run experiments. These have not yet been verified because no API experiment has been run.

## 8. What worked and what did not work

No Gemini outputs have been collected, so there is not yet evidence to report about model behavior. API failures, when attempted, are stored and included in a regenerated report.

## 9. Conclusion

This is an initial report template, not an experiment-results claim. Configure `GEMINI_API_KEY`, run the benchmark buttons in the application, and regenerate this report to include actual Gemini outputs and measured results.
