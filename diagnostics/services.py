import logging

logger = logging.getLogger('diagnostics.external')


def log_external_api_call(name, url, method='GET', response=None, duration_ms=None, metadata=None):
    """Log external API interactions in a structured way."""

    payload = {
        'external_name': name,
        'url': url,
        'method': method,
    }
    if response is not None:
        payload['status_code'] = getattr(response, 'status_code', None)
        try:
            payload['body'] = response.json()
        except Exception:
            payload['body'] = getattr(response, 'text', str(response))
    if metadata:
        payload.update(metadata)

    logger.info(
        'External API interaction logged',
        extra={
            'metadata': payload,
            'external_service': name,
            'response_status': payload.get('status_code'),
            'duration_ms': duration_ms,
        },
    )
