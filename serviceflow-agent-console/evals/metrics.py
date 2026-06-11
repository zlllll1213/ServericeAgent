from __future__ import annotations

from collections import Counter


def accuracy(pairs: list[tuple[str, str]]) -> float:
    return round(sum(1 for expected, actual in pairs if expected == actual) / len(pairs), 4) if pairs else 0.0


def confusion_matrix(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    matrix: dict[str, Counter] = {}
    for expected, actual in pairs:
        matrix.setdefault(expected, Counter())[actual] += 1
    return {key: dict(value) for key, value in matrix.items()}


def rate(values: list[bool]) -> float:
    return round(sum(1 for value in values if value) / len(values), 4) if values else 0.0
