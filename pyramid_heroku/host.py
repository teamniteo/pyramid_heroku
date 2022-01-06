"""Set request.host from X-Forwarded-Host."""


def includeme(config):
    config.add_tween("pyramid_heroku.host.Host")


class Host(object):
    """Set request.host to proxied X-Forwarded-Host header.

    The tween checks if `X-Forwarded-Host` is present and if it is,
    overwrites the value of request.host with the value from the header.

    Note that this is a potential security risk in some environments and
    the `X-Forwarded-Host` header is not trusted by Heroku's Load Balancer:
    https://devcenter.heroku.com/articles/http-routing#heroku-headers

    The reason we need this is to support AutoIdle's Custom Domains:
    https://github.com/teamniteo/pyramid-realworld-example-app/issues/127#issuecomment-711894122
    """

    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry

    def __call__(self, request):
        if request.headers.get("X-Forwarded-Host"):
            request.host = request.headers["X-Forwarded-Host"]
        return self.handler(request)
