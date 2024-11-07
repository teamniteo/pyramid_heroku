"""Prevent .herokuapp.com access to non-allowlisted IPs"""

from pyramid.response import Response

import logging


def includeme(config):
    config.add_tween("pyramid_heroku.herokuapp_access.HerokuappAccess")


class HerokuappAccess(object):
    """Deny access to 'herokuapp.com' urls for IPs that are not allowlisted.

    Denies access to hosts that contain 'herokuapp.com' to ips that are not
    allowlisted. Registry settings must contain a key
    'pyramid_heroku.herokuapp_allowlist', whose value must be a list of
    strings (IPs). For this tween to work, you must include the
    ClientAddr tween and make sure this tween executes after the ClientAddr
    tween.
    """

    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry
        self.settings = getattr(registry, "settings", {})

    def __call__(self, request):
        allowlisted_ips = request.registry.settings.get(
            "pyramid_heroku.herokuapp_allowlist", []
        )

        if (
            "herokuapp.com" in request.headers["Host"]
            and request.client_addr not in allowlisted_ips
        ):
            if request.registry.settings.get("pyramid_heroku.structlog"):
                import structlog

                logger = structlog.getLogger(__name__)
                logger.info(
                    "Herokuapp access denied",
                    user_ip=request.client_addr,
                    host=request.headers["Host"],
                )
            else:
                logger = logging.getLogger(__name__)
                logger.info(
                    f'Denied Herokuapp access for Host {request.headers["Host"]}'
                    f" and IP {request.client_addr}"
                )

            resp = Response("Unauthorized.", status=403, content_type="text/plain")
            resp.status = "403 Unauthorized"
            return resp

        return self.handler(request)
