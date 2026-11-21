# Prompt Engineering Mastery Lab

A beginner-friendly, hands-on Streamlit application that compares three prompt engineering techniques using actual Google Gemini API calls. It is an experiment lab, not a chatbot: each run shows its prompt and real model output, checks results where possible, and appends every attempt to a local JSON log.

## Features

1. **Zero-shot vs Few-shot:** compare sentiment classification with and without five labeled examples. Run a custom review or the five-case benchmark.
2. **Chain-of-Thought:** compare direct answers to concise key calculation steps on five math word problems. Python checks parsed answers against expected values. The prompts do not request private internal reasoning.
3. **Structured Output:** extract transaction information with Gemini's JSON response mode and a JSON schema. Python parses and checks the response.
4. **Results & Analysis:** view saved attempts, math and sentiment accuracy, JSON validity rate, and generate/download a Markdown report.
5. **Append-only tracking:** successful responses and failed API attempts are recorded in `data/experiments.json`.

Model responses are never simulated. The initial report says that experiments have not yet run until actual API attempts are saved.

## Technologies

- Python
- Streamlit
- Google GenAI SDK (`google-genai`) and Gemini Interactions API
- JSON and Pandas
- python-dotenv

## Project structure

```text
.
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── modules/
│   ├── __init__.py
│   ├── gemini_client.py
│   ├── zero_few_shot.py
│   ├── reasoning.py
│   ├── structured_output.py
│   ├── experiment_tracker.py
│   └── report_generator.py
├── data/
│   └── experiments.json
├── reports/
│   └── PROMPT_ENGINEERING_REPORT.md
└── README.md
```

## Installation

Open a terminal in this project folder. Create and activate a Python 3.13 virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the requirements:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure the Gemini API key

Create a key in [Google AI Studio](https://aistudio.google.com/apikey). Add it to the root `.env` file:

```dotenv
GEMINI_API_KEY=put_your_real_key_here
GEMINI_MODEL=gemini-4-hydrogen
```

The `.env` file is ignored by Git. Never paste the API key into the app, source code, screenshots, or a commit. The model can be changed through `GEMINI_MODEL` if needed. The dashboard theme can be changed in `.streamlit/config.toml`.

## Run the application

```powershell
python -m streamlit run app.py
```

Streamlit opens the local app in your browser. The sidebar contains Dashboard, Zero-shot vs Few-shot, Chain-of-Thought, Structured Output, and Results & Analysis.

## Run the experiments

- **Sentiment:** enter a review and click **Run comparison** for two API calls, or **Run all 5 test sentences** for ten calls.
- **Math:** select a problem and click **Run both prompts** for two API calls, or **Run all 5 math problems** for ten calls.
- **JSON extraction:** enter text and click **Extract fields**, or click **Run all 5 test inputs**.
- **Results:** inspect the log and measured rates. Run requests only after configuring a working API key.

API usage may incur charges and is subject to Google's model availability and quota. Each API request may fail; failures are retained and are not represented as model outputs. JSON success rate measures parsing and the required fields/types, not semantic correctness. Math accuracy only uses answers that Python can parse; unparseable answers are marked unverifiable.

### Missing JSON values

The output schema requires a numeric `amount`. When the source text does not state an amount, the prompt uses `0` as a sentinel and asks the model to say in `description` that the amount was not provided. Missing text values use empty strings. This policy avoids inventing a payment amount.

## Generate the final report

Open **Results & Analysis**, then click **Generate PROMPT_ENGINEERING_REPORT.md**. The report is written to `reports/PROMPT_ENGINEERING_REPORT.md` from the saved experiment log. It preserves the exact prompts and raw outputs, includes failed API attempts, and labels sections with no saved runs as **Not yet run**. Generate it again after running more experiments to refresh the snapshot.

## Screenshots

Add screenshots of the Dashboard, technique pages, and Results & Analysis here after running the application. Do not include an API key in screenshots.

## Example experiments

The application includes five built-in sentiment sentences, five multi-step math questions, and five messy transaction inputs. The initial report contains no fabricated examples or sample model responses; actual prompts and outputs appear only after you run the Gemini API experiments.

## GitHub repository instructions

1. Create a new, empty repository on GitHub.
2. From this folder, initialize Git and make an initial commit:

   ```powershell
   git init
   git add app.py modules data reports README.md requirements.txt .env.example .gitignore
   git commit -m "Build Prompt Engineering Mastery Lab"
   ```
3. Add your repository as the remote and push the branch:

   ```powershell
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git branch -M main
   git push -u origin main
   ```

The local `.env` is excluded from the command and ignored by Git; do not commit it.
