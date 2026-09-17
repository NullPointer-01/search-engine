import os

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = os.getenv("ES_PORT", "9200")
ES_INDEX = os.getenv("ES_INDEX", "search")

MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50))
