import threading

_thread_local = threading.local()


def get_current_user():
    """Return the current request's user from thread-local storage."""
    return getattr(_thread_local, 'user', None)


class CurrentUserMiddleware:
    """
    Middleware that stores request.user in thread-local storage.
    Used by audit tracking to auto-populate created_by/updated_by
    without passing request through service layers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.user = getattr(request, 'user', None)
        response = self.get_response(request)
        # Clean up after request
        _thread_local.user = None
        return response
