from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, TypeAlias, cast

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class StrictJsonLimits:
    max_bytes: int
    max_depth: int
    max_nodes: int

    def __post_init__(self) -> None:
        if self.max_bytes < 1 or self.max_depth < 1 or self.max_nodes < 1:
            raise ValueError("strict JSON limits must be positive")


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicates(
    pairs: list[tuple[str, JsonValue]],
) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _validate_tree(value: JsonValue, limits: StrictJsonLimits) -> None:
    stack: list[tuple[JsonValue, int]] = [(value, 1)]
    node_count = 0
    while stack:
        current, depth = stack.pop()
        node_count += 1
        if node_count > limits.max_nodes:
            raise ValueError("JSON value exceeds the node-count limit")
        if depth > limits.max_depth:
            raise ValueError("JSON value exceeds the nesting-depth limit")

        if isinstance(current, float) and not math.isfinite(current):
            raise ValueError("non-finite JSON number is forbidden")
        if isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
        elif isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())


def parse_json_bytes(data: bytes, limits: StrictJsonLimits) -> JsonValue:
    if len(data) > limits.max_bytes:
        raise ValueError("JSON input exceeds the byte-size limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("JSON input must be valid UTF-8") from exc
    try:
        payload: object = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    value = cast(JsonValue, payload)
    _validate_tree(value, limits)
    return value


def parse_json_object_bytes(data: bytes, limits: StrictJsonLimits) -> JsonObject:
    payload = parse_json_bytes(data, limits)
    if not isinstance(payload, dict):
        raise ValueError("JSON input must contain an object")
    return payload


def load_json_path(path: Path, limits: StrictJsonLimits) -> JsonValue:
    return parse_json_bytes(path.read_bytes(), limits)


def load_json_object_path(path: Path, limits: StrictJsonLimits) -> JsonObject:
    return parse_json_object_bytes(path.read_bytes(), limits)


def load_json_object_stream(
    stream: BinaryIO,
    limits: StrictJsonLimits,
) -> JsonObject:
    data = stream.read(limits.max_bytes + 1)
    return parse_json_object_bytes(data, limits)
