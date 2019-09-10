"""Set request ID in Sentry logs if sentry is imported, and in structlog logs
if structlog is imported.
"""


try:
    import sentry_sdk
    IS_SENTRY_ENABLED = True
except ImportError:
    IS_SENTRY_ENABLED = False

try:
    import structlog
    IS_STRUCTLOG_ENABLED = True
except ImportError:
    IS_STRUCTLOG_ENABLED = False


def includeme(config):
    config.add_tween("pyramid_heroku.request_id.RequestIDLogger")


class RequestIDLogger(object):
    """Set request ID in sentry and structlog logs.

    If the request headers contain a request ID (X-Request-ID), it should be
    logged for better debugging. In case sentry is being used, log the request
    ID along with other info. Similarly, if structlog is being used, add the
    request ID in the logs.
    """

    def __init__(self, handler, _):
        self.handler = handler

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID")

        if request_id is not None:
            if IS_SENTRY_ENABLED:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_tag("request_id", request_id)

            if IS_STRUCTLOG_ENABLED:
                WrappedDictClass = structlog.threadlocal.wrap_dict(dict)
                wrapped_request_id = WrappedDictClass({
                    "request_id": request_id
                })
                structlog.configure(context_class=WrappedDictClass)

        return self.handler(request)
