"""Direct and concise step-by-step math prompts and answer checking."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class MathProblem:
    name: str
    question: str
    expected_answer: str


MATH_PROBLEMS = [
    MathProblem(
        "Notebooks",
        "A classroom has 48 notebooks. The teacher buys 6 packs with 8 notebooks "
        "each, then gives 17 notebooks to students. How many notebooks remain?",
        "79",
    ),
    MathProblem(
        "Bus seats",
        "Three buses each have 42 seats. If 108 tickets are sold and every ticket "
        "holder boards a bus, how many seats are empty?",
        "18",
    ),
    MathProblem(
        "Sale and tax",
        "A jacket costs $36. It is discounted by 25%, then 8% sales tax is applied "
        "to the discounted price. What is the final price in dollars?",
        "29.16",
    ),
    MathProblem(
        "Cookies",
        "A bakery makes 5 trays with 24 cookies on each tray. The cookies are "
        "shared equally among 8 classes. How many cookies does each class get?",
        "15",
    ),
    MathProblem(
        "Road trip",
        "A car travels 315 km at a steady 70 km per hour. How many hours does the "
        "trip take?",
        "4.5",
    ),
]

_NUMBER_PATTERN = r"[-+]?\d[\d,]*(?:\.\d+)?"


def build_direct_prompt(question: str) -> str:
    """Ask for only the final numerical answer."""
    return (
        "Solve this math word problem. Reply with only the final numerical "
        f"answer (include a unit only if essential).\n\nProblem: {question}"
    )


def build_step_by_step_prompt(question: str) -> str:
    """Ask for a short explanation of key calculations, not private reasoning."""
    return (
        "Solve this math word problem. Give a concise explanation containing "
        "only the key calculation steps, then end with a line in this exact "
        "format: Final answer: <number>. Do not provide private internal "
        f"reasoning.\n\nProblem: {question}"
    )


def extract_numerical_answer(output: str) -> Decimal | None:
    """Read the labeled final answer, or the last number if no label is present."""
    labeled = re.search(
        rf"final\s+answer\s*(?:is|:)?\s*({_NUMBER_PATTERN})",
        output,
        flags=re.IGNORECASE,
    )
    matches = re.findall(_NUMBER_PATTERN, output)
    if labeled:
        candidate = labeled.group(1)
    elif matches:
        candidate = matches[-1]
    else:
        return None

    try:
        return Decimal(candidate.replace(",", ""))
    except InvalidOperation:
        return None


def is_correct_math_answer(output: str, expected_answer: str) -> bool | None:
    """Compare a parsed answer with the known answer; None means unparseable."""
    actual = extract_numerical_answer(output)
    if actual is None:
        return None
    return actual == Decimal(expected_answer)
