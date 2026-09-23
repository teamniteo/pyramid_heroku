"""Prevent access to the hosting platform's own domain for non-allowlisted IPs."""

from pyramid.response import Response
from pyramid.tweens import INGRESS

import logging
import os

#: Hostnames gated when the app does not say otherwise. Heroku's own, so
#: existing apps keep their behaviour.
DEFAULT_HOSTS = "herokuapp.com"


def includeme(config):
    # Below client_addr when it is present, so that request.client_addr is
    # already the real caller. Platforms that hand us the caller in a header
    # need no client_addr tween, and the tween then lands under INGRESS.
    config.add_tween(
        "pyramid_heroku.herokuapp_access.HerokuappAccess",
        under=("pyramid_heroku.client_addr.ClientAddr", INGRESS),
    )


class HerokuappAccess(object):
    """Deny access to the platform's own hostnames for IPs that are not allowlisted.

    Review apps live on the platform's own domain, which Cloudflare Access
    cannot be configured for in advance, so they are gated on an IP allowlist
    instead. Settings:

    ``pyramid_heroku.herokuapp_hosts``
        Whitespace separated hostnames to gate, matched as whole domain
        labels, so ``fly.dev`` matches ``foo.fly.dev`` but not
        ``fly.dev.attacker.example``. Defaults to ``herokuapp.com``. Naming
        hosts replaces the default rather than adding to it.

    ``pyramid_heroku.herokuapp_allowlist``
        Whitespace separated IPs allowed on those hostnames. Missing or empty
        denies everyone.

    ``pyramid_heroku.client_addr_header``
        Header to read the caller's IP from instead of ``request.client_addr``.
        Fly.io's proxy rewrites ``X-Forwarded-For`` to its own address, so the
        caller never appears there, but it overwrites ``Fly-Client-IP`` on
        every request, which makes that header safe to trust. Only set this on
        a platform that guarantees the header: anywhere else the caller can
        send it themselves.

    A bypass is possible by setting the ``HEROKUAPP_ACCESS_BYPASS`` environment
    variable to a secret and sending it as the ``User-Agent``.
    """

    import os

    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry
        self.settings = getattr(registry, "settings", {})

    def gated(self, request):
        """Report whether this request's hostname is one we gate."""
        settings = request.registry.settings
        hosts = settings.get("pyramid_heroku.herokuapp_hosts", DEFAULT_HOSTS).split()

        # A Host header may carry a port, which is not part of the hostname.
        host = request.headers.get("Host", "").split(":")[0]

        return any(host == h or host.endswith("." + h) for h in hosts)

    def client_addr(self, request):
        """Get the caller's IP from the configured header, else from Pyramid."""
        header = request.registry.settings.get("pyramid_heroku.client_addr_header")
        if header:
            return request.headers.get(header)
        return request.client_addr

    def __call__(self, request):
        allowlisted_ips = request.registry.settings.get(
            "pyramid_heroku.herokuapp_allowlist", ""
        ).split()

        if os.environ.get("HEROKUAPP_ACCESS_BYPASS"):
            if request.headers.get("User-Agent") == os.environ.get(
                "HEROKUAPP_ACCESS_BYPASS"
            ):
                if request.registry.settings.get("pyramid_heroku.structlog"):
                    import structlog

                    logger = structlog.getLogger(__name__)
                    logger.info(
                        "Herokuapp access bypassed", user_ip=request.client_addr
                    )
                else:
                    logger = logging.getLogger(__name__)
                    logger.info(f"Herokuapp access bypassed by {request.client_addr}")

                return self.handler(request)

        if self.gated(request):
            client_addr = self.client_addr(request)
            host = request.headers.get("Host", "")
            if client_addr not in allowlisted_ips:
                if request.registry.settings.get("pyramid_heroku.structlog"):
                    import structlog

                    logger = structlog.getLogger(__name__)
                    logger.info(
                        "Herokuapp access denied",
                        user_ip=client_addr,
                        allowed_ips=", ".join(allowlisted_ips),
                        host=host,
                    )
                else:
                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"Denied Herokuapp access for Host {host}"
                        f" and IP {client_addr}"
                    )

                resp = Response("Unauthorized.", status=403, content_type="text/plain")
                resp.status = "403 Unauthorized"
                return resp

        return self.handler(request)
