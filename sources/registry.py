from typing import List
from sources.base import BaseSource
from sources.shmtranslations import ShmTranslationsSource
from sources.novelupdates import NovelUpdatesSource
from sources.novelfull import NovelFullSource


SOURCES: List[BaseSource] = [
    ShmTranslationsSource(),
    NovelFullSource(),
    NovelUpdatesSource(),
]


def get_source_for_url(url: str) -> BaseSource:
    for source in SOURCES:
        if source.matches(url):
            return source
    return None