from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

BUSINESS_EVENT_COUNT = Counter(
    "business_events_total",
    "Total number of business endpoint hits",
    ["event_type"],
)


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
