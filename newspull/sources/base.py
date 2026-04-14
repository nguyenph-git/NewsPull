from abc import ABC, abstractmethod
from ..models import RawArticle


class Source(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch(self) -> list[RawArticle]: ...
