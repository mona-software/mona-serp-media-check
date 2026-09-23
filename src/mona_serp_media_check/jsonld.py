"""Tien ich doc va duyet cac khoi JSON-LD (structured data)."""

from __future__ import annotations

import json


def parse_blocks(raw_blocks: list[str]) -> tuple[list[dict], list[str]]:
    """Parse tung khoi JSON-LD bang json.loads.

    Tra ve (danh sach object da parse duoc, danh sach loi cu phap).
    Loi cu phap duoc bao cao rieng vi mot khoi JSON-LD hong cu phap la
    van de nghiem trong: cong cu tim kiem se bo qua toan bo khoi do.
    """
    parsed = []
    errors = []
    for i, raw in enumerate(raw_blocks):
        try:
            parsed.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            errors.append(f"khoi JSON-LD #{i + 1}: {exc}")
    return parsed, errors


def iter_nodes(data) -> list[dict]:
    """Duyet de quy moi node co @type, gom ca @graph va cac list long nhau.

    Mot trang co the khai ImageObject/VideoObject o nhieu tang: ngay tai
    goc, trong mang, trong @graph, hoac long ben trong mot thuoc tinh
    cua node khac (vi du Article.image = {"@type": "ImageObject", ...}).
    """
    nodes: list[dict] = []

    def walk(node):
        if isinstance(node, dict):
            if "@type" in node:
                nodes.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return nodes


def nodes_of_type(parsed_blocks: list, type_name: str) -> list[dict]:
    result = []
    for block in parsed_blocks:
        for node in iter_nodes(block):
            type_value = node.get("@type")
            if type_value == type_name:
                result.append(node)
            elif isinstance(type_value, list) and type_name in type_value:
                result.append(node)
    return result
