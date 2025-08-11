import json
import threading
import time
from collections import defaultdict
from pathlib import Path

from fastapi import HTTPException, Request, status

RATE_LIMIT_FILE = Path("rate_limits.json")
_request_storage: dict[str, list[float]] = defaultdict(list)
_storage_lock = threading.Lock()


def _load_rate_limits():
    """Load rate limits from persistent storage on startup."""
    global _request_storage
    if RATE_LIMIT_FILE.exists():
        try:
            with RATE_LIMIT_FILE.open() as f:
                data = json.load(f)
                _request_storage = defaultdict(list, data)
        except (json.JSONDecodeError, OSError):
            # If file is corrupted, start fresh
            _request_storage = defaultdict(list)


def _save_rate_limits():
    """Save current rate limits to persistent storage."""
    try:
        with RATE_LIMIT_FILE.open("w") as f:
            json.dump(dict(_request_storage), f)
    except OSError:
        # If we can't save, continue without persistence
        pass


# Load existing rate limits on module import
_load_rate_limits()


def _get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    if request.client:
        return request.client.host
    return "unknown"


def _clean_old_requests(ip: str, window_seconds: int):
    """Remove requests older than the time window."""
    current_time = time.time()
    with _storage_lock:
        _request_storage[ip] = [
            timestamp
            for timestamp in _request_storage[ip]
            if current_time - timestamp < window_seconds
        ]


def _cleanup_expired_entries():
    """Remove all expired entries from storage and save to disk."""
    current_time = time.time()
    with _storage_lock:
        # Remove all entries older than 1 hour (3600 seconds)
        keys_to_remove = []
        for ip, timestamps in _request_storage.items():
            _request_storage[ip] = [
                timestamp for timestamp in timestamps if current_time - timestamp < 3600
            ]
            # If no timestamps left, mark for removal
            if not _request_storage[ip]:
                keys_to_remove.append(ip)

        # Remove empty entries
        for ip in keys_to_remove:
            del _request_storage[ip]

        # Save cleaned state to disk
        _save_rate_limits()


def _add_request_timestamp(ip: str):
    """Thread-safely add a request timestamp and save to disk."""
    with _storage_lock:
        _request_storage[ip].append(time.time())
        _save_rate_limits()


def login_rate_limit(request: Request):
    """Rate limit login requests: 5 requests per minute."""
    ip = _get_client_ip(request)
    _clean_old_requests(ip, 60)  # 60 seconds window

    with _storage_lock:
        request_count = len(_request_storage[ip])

    if request_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    _add_request_timestamp(ip)

    # Periodic cleanup (every 50th request approximately)
    if request_count % 50 == 0:
        _cleanup_expired_entries()


def general_rate_limit(request: Request):
    """Rate limit general requests: 60 requests per minute."""
    ip = _get_client_ip(request)
    _clean_old_requests(ip, 60)  # 60 seconds (1 minute) window

    with _storage_lock:
        request_count = len(_request_storage[ip])

    if request_count >= 60:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    _add_request_timestamp(ip)

    # Periodic cleanup (every 100th request approximately)
    if request_count % 100 == 0:
        _cleanup_expired_entries()
