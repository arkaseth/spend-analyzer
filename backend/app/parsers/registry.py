from typing import Optional
from app.parsers.base import BaseParser


_parsers: dict[str, type[BaseParser]] = {}


def register(parser_class: type[BaseParser]):
    _parsers[parser_class.bank_name.lower()] = parser_class
    return parser_class


def get_parser(bank_name: str) -> Optional[type[BaseParser]]:
    return _parsers.get(bank_name.lower())


def all_parsers() -> dict[str, type[BaseParser]]:
    return dict(_parsers)


def detect_parser(text: str) -> Optional[type[BaseParser]]:
    for parser_cls in _parsers.values():
        if parser_cls.can_parse(text):
            return parser_cls
    return None
