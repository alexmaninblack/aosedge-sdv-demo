# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Source-only checks of current private admin schemas; never a runtime client.

This deliberately closed JSON Schema subset covers only current-admin.schema.json.
Unknown keywords fail rather than silently skipping a constraint. Stateful token,
context/selector and transaction authority still belongs to each backend.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re


class ContractError(ValueError):
    pass


KEYWORDS = {"$schema", "$id", "$comment", "$defs", "$ref", "title", "description",
            "type", "const", "enum", "properties", "required", "additionalProperties",
            "items", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength",
            "minimum", "pattern", "format", "allOf", "not", "if", "then", "else"}


def document(path: Path):
    def pairs(rows):
        value = {}
        for key, item in rows:
            if key in value:
                raise ContractError("duplicate JSON key: " + key)
            value[key] = item
        return value
    return json.loads(path.read_text(), object_pairs_hook=pairs)


def schema_keywords(schema):
    """Inspect even conditional branches not selected by a positive fixture."""
    if not isinstance(schema, dict) or set(schema) - KEYWORDS:
        raise ContractError("unsupported schema keyword")
    for key in ("$defs", "properties"):
        for child in schema.get(key, {}).values():
            schema_keywords(child)
    for key in ("items", "not", "if", "then", "else"):
        if key in schema:
            schema_keywords(schema[key])
    for child in schema.get("allOf", []):
        schema_keywords(child)


def validate(value, schema, root=None):
    root = schema if root is None else root
    if set(schema) - KEYWORDS:
        raise ContractError("unsupported schema keyword")
    if "$ref" in schema:
        target = schema["$ref"]
        if not target.startswith("#/$defs/") or target.count("/") != 2:
            raise ContractError("only local definition references are supported")
        validate(value, root["$defs"][target.split("/")[-1]], root)
    kinds = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    if "type" in schema and type(value) is not kinds[schema["type"]]:
        raise ContractError("invalid type")
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        raise ContractError("invalid constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError("invalid enum")
    if isinstance(value, dict):
        if not set(schema.get("required", [])) <= set(value):
            raise ContractError("missing field")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise ContractError("unknown field")
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], root)
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", len(value)):
            raise ContractError("invalid array size")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            raise ContractError("duplicate array item")
        if "items" in schema:
            for item in value:
                validate(item, schema["items"], root)
    if isinstance(value, str):
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", len(value)):
            raise ContractError("invalid string size")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise ContractError("invalid pattern")
        if "format" in schema:
            if schema["format"] != "date-time":
                raise ContractError("unsupported format")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if "T" not in value or parsed.tzinfo is None:
                    raise ValueError()
            except ValueError as exc:
                raise ContractError("invalid date-time") from exc
    if type(value) is int and value < schema.get("minimum", value):
        raise ContractError("below minimum")
    for child in schema.get("allOf", []):
        validate(value, child, root)
    if "not" in schema:
        try:
            validate(value, schema["not"], root)
        except ContractError:
            pass
        else:
            raise ContractError("forbidden shape")
    if "if" in schema:
        try:
            validate(value, schema["if"], root)
            branch = "then"
        except ContractError:
            branch = "else"
        if branch in schema:
            validate(value, schema[branch], root)


def check(root: Path, workspace=False):
    """Return errors; inspect only small tracked metadata/source declarations."""
    errors = []
    for team in ("brake", "tire"):
        folder = root / "contracts" / (team + "-cloud-api")
        try:
            profile = document(folder / "current-admin-profile.v1.json")
            schema = document(folder / profile["schema"])
            schema_keywords(schema)
            fixtures = document(folder / profile["fixtures"])
            for name, value in fixtures.items():
                if name != "$comment":
                    validate(value, {"$ref": "#/$defs/" + name}, schema)
            counts = schema["$defs"]["recordCounts"]
            if set(profile["recordCategories"]) != set(counts["properties"]) or len(counts["required"]) != 10:
                raise ContractError("profile/schema category mismatch")
            for endpoint in profile["endpoints"].values():
                for key in ("request", "response"):
                    if endpoint[key].split("/")[-1] not in schema["$defs"]:
                        raise ContractError("missing endpoint schema")
            if workspace:
                if team == "brake":
                    source = root.parent / "brake-health-cloud/apps/backend/src/brake-data-store.ts"
                    match = re.search(r'const TABLES = (\[[^;]+\]) as const;', source.read_text())
                    actual = json.loads(match[1]) if match else []
                else:
                    source = root.parent / "tire-health-cloud/src/store.mjs"
                    match = re.search(r'const categories = \{([^}]+)\}', source.read_text())
                    actual = re.findall(r'(\w+):', match[1]) if match else []
                if actual != profile["recordCategories"]:
                    raise ContractError("backend category declaration differs from current profile")
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors.append(f"{team} current admin contract: {exc}")
    return errors
