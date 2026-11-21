"""Prompt builders and examples for sentiment classification."""

TEST_SENTENCES = [
    {
        "input": "The package arrived early and the quality is excellent.",
        "expected": "Positive",
    },
    {
        "input": "This was a frustrating purchase; it stopped working immediately.",
        "expected": "Negative",
    },
    {
        "input": "The item is blue and weighs about two kilograms.",
        "expected": "Neutral",
    },
    {
        "input": "Friendly staff, quick service, and a delicious lunch.",
        "expected": "Positive",
    },
    {
        "input": "The room was dirty and the booking was cancelled without notice.",
        "expected": "Negative",
    },
]

FEW_SHOT_EXAMPLES = [
    ("I love how easy this app is to use.", "Positive"),
    ("The food was cold and the service was rude.", "Negative"),
    ("My appointment is scheduled for Thursday.", "Neutral"),
    ("The staff were helpful and solved my problem quickly.", "Positive"),
    ("The delivery was late and the box was damaged.", "Negative"),
]


def build_zero_shot_prompt(text: str) -> str:
    """Build a classification prompt without labeled examples."""
    return (
        "Classify the sentiment of the text below as exactly one of: "
        "Positive, Negative, or Neutral. Reply with only the label.\n\n"
        f"Text: {text}"
    )


def build_few_shot_prompt(text: str) -> str:
    """Build the same classification task with five labeled examples."""
    examples = "\n".join(
        f'Text: "{example}"\nSentiment: {label}'
        for example, label in FEW_SHOT_EXAMPLES
    )
    return (
        "Classify the sentiment of the final text as exactly one of: Positive, "
        "Negative, or Neutral. Reply with only the label. Use these examples "
        "as demonstrations; classify the final text, not an example.\n\n"
        f"{examples}\n\nText: {text}\nSentiment:"
    )


def extract_sentiment(output: str) -> str | None:
    """Return a recognized label only when the complete answer is that label."""
    label = output.strip().strip(" .!").casefold()
    labels = {"positive": "Positive", "negative": "Negative", "neutral": "Neutral"}
    return labels.get(label)
