from __future__ import annotations

import re


VALID_CHARS = re.compile(r"^[A-Za-z0-9_(),.\-+/*<>=\s]+$")
KNOWN_OPERATORS = {
    "rank",
    "zscore",
    "ts_mean",
    "ts_delta",
    "ts_std_dev",
    "ts_corr",
    "close",
    "returns",
    "volume",
    "vwap",
}


class ExpressionValidator:
    def validate(self, expression: str) -> list[str]:
        errors: list[str] = []
        if not expression:
            return ["Expression is empty."]
        if not VALID_CHARS.match(expression):
            errors.append("Expression contains unsupported characters.")
        if expression.count("(") != expression.count(")"):
            errors.append("Parentheses are unbalanced.")

        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression)
        unknown = [
            token for token in tokens
            if token.islower() and token not in KNOWN_OPERATORS
        ]
        if unknown:
            errors.append(f"Unknown tokens detected: {', '.join(sorted(set(unknown))[:5])}")
        return errors

