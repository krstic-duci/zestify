import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_request_storage: dict[str, list[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    if request.client:
        return request.client.host
    return "unknown"


def _clean_old_requests(ip: str, window_seconds: int):
    """Remove requests older than the time window."""
    current_time = time.time()
    _request_storage[ip] = [
        timestamp
        for timestamp in _request_storage[ip]
        if current_time - timestamp < window_seconds
    ]


def login_rate_limit(request: Request):
    """Rate limit login requests: 5 requests per minute."""
    ip = _get_client_ip(request)
    _clean_old_requests(ip, 60)  # 60 seconds window

    if len(_request_storage[ip]) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    _request_storage[ip].append(time.time())


def general_rate_limit(request: Request):
    """Rate limit general requests: 10 requests per minute."""
    ip = _get_client_ip(request)
    _clean_old_requests(ip, 60)  # 60 seconds (1 minute) window

    if len(_request_storage[ip]) >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    _request_storage[ip].append(time.time())
