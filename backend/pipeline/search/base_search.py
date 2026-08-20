class SearchResult:
    def __init__(self, url, title, snippet, source_provider):
        self.url = url
        self.title = title
        self.snippet = snippet
        self.source_provider = source_provider

class BaseSearchProvider:
    name: str
    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        raise NotImplementedError
