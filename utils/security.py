from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from utils.config import SETTINGS

    environment = getattr(SETTINGS, "env", "dev")
except (ImportError, AttributeError):
    environment = "dev"

SECURITY_HEADERS = {
    # X-Content-Type-Options: Prevents browsers from MIME-sniffing a response away from the declared content-type.
    "X-Content-Type-Options": "nosniff",
    # X-Frame-Options: Prevents the site from being rendered in a frame to protect against clickjacking attacks.
    "X-Frame-Options": "DENY",
    # X-XSS-Protection: Enables the browser's cross-site scripting (XSS) filter and blocks detected attacks.
    "X-XSS-Protection": "1; mode=block",
    # Referrer-Policy: Controls what information about the current page's URL is shared when navigating to other sites.
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

if environment == "prod":
    SECURITY_HEADERS["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "  # Allow Sortable.js CDN
    "style-src 'self' ; "
    "img-src 'self' data: https:; "  # Allow images from HTTPS and data URLs
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        # NOTE: Relax CSP for Swagger docs
        if request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = CSP_POLICY
        return response
