from abc import ABC, abstractmethod
from typing import List
from models.schemas import Novel, ChapterRef, ChapterContent


class BaseSource(ABC):
    @abstractmethod
    def matches(self, url: str) -> bool:
        pass

    @abstractmethod
    def get_novel_metadata(self, url: str) -> Novel:
        pass

    @abstractmethod
    def get_chapter_list(self, url: str) -> List[ChapterRef]:
        pass

    @abstractmethod
    def get_chapter_content(self, chapter_url: str) -> ChapterContent:
        pass