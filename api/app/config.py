import os

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = os.getenv("ES_PORT", "9200")
ES_INDEX = os.getenv("ES_INDEX", "search")

MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50))
HIGHLIGHT_FRAGMENTS_COUNT = int(os.getenv("HIGHLIGHT_FRAGMENTS_COUNT", 2))
HIGHLIGHT_FRAGMENTS_SIZE = int(os.getenv("HIGHLIGHT_FRAGMENTS_SIZE", 200))

# Characters analyzed per field when highlighting
HIGHLIGHT_MAX_ANALYZED_CHARS = int(os.getenv("HIGHLIGHT_MAX_ANALYZED_CHARS", 1000000))
