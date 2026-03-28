from typing import List
from sources.base import BaseSource
from sources.shmtranslations import ShmTranslationsSource
from sources.novelupdates import NovelUpdatesSource
from sources.novelfull import NovelFullSource
from sources.syosetu import SyosetuSource


# Source Registry
# This file maintains the list of all supported novel sources.
# When a user provides a URL, the system checks each source to see
# which one can handle the URL and routes the request to the correct scraper.

SOURCES: List[BaseSource] = [
    ShmTranslationsSource(),
    NovelFullSource(),
    NovelUpdatesSource(),
    SyosetuSource(),
]


def get_source_for_url(url: str) -> BaseSource:
    """
    Return the appropriate Source implementation for a given URL.
    Called by main.py to determine which scraper should handle the novel.
    """
    for source in SOURCES:
        if source.matches(url):
            return source
    return None
