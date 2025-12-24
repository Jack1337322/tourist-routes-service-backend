"""
Middleware to log all incoming requests for debugging.
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests.
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            logger.info(
                f"API Request: {request.method} {request.path} | "
                f"Origin: {request.META.get('HTTP_ORIGIN', 'N/A')} | "
                f"Content-Type: {request.META.get('CONTENT_TYPE', 'N/A')} | "
                f"Body: {getattr(request, 'body', b'').decode('utf-8', errors='ignore')[:200]}"
            )
        return None

    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            logger.info(
                f"API Response: {request.method} {request.path} | "
                f"Status: {response.status_code}"
            )
        return response

