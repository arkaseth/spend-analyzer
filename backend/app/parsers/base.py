from abc import ABC, abstractmethod
from typing import Optional


class BaseParser(ABC):
    bank_name: str = ""
    account_type: str = ""

    @classmethod
    @abstractmethod
    def can_parse(cls, text: str) -> bool:
        pass

    @abstractmethod
    def parse(self, text: str) -> list[dict]:
        pass
