def request_id(request):
    """Expose the current request_id to templates."""
    return {'request_id': getattr(request, 'request_id', '')}
