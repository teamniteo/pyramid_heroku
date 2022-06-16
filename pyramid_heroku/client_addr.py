"""Set client_addr IP that we can trust."""
from ipaddress import IPv4Address
from ipaddress import IPv4Network

import logging
import requests


def includeme(config):
    config.add_tween("pyramid_heroku.client_addr.ClientAddr")


class ClientAddr(object):
    """Set request.client_addr to an IP we can trust.

    Sets correct IP to request.client_addr when running on Heroku with
    gunicorn. Should execute before other tweens which depend on it. This can
    be achieved with :ref:`Explicit tween ordering
    <pyramid:explicit_tween_ordering>` or by passing 'over' and 'under'
    arguments to :py:meth:`config.Configurator.add_tween` like this

    .. code-block:: python

        config.add_tween(
            'pyramid_heroku.client_addr.ClientAddr',
            under=pyramid.tweens.INGRESS,
        )

    The tween checks if ``X-Forwarded-For`` is present and if it is, it
    filters out any Cloudflare IPs and takes the last IP in the
    ``X-Forwarded-For`` list and makes it the only IP in the list.

    Cloudflare IPs are filtered out to avoid setting Cloudflare IP in
    ``X-Forwarded-For`` when using Cloudflare's reverse proxy.

    This effectively causes pyramid to return this real IP for
    ``request.client_addr``. Read rationale behind why we do this on
    https://github.com/teamniteo/heroku_ips.
    """

    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry
        self.ignored_ip_networks = self.get_cloudflare_ip_networks()

    def __call__(self, request):
        if request.headers.get("X-Forwarded-For"):
            ips = [ip.strip() for ip in request.headers["X-Forwarded-For"].split(",")]
            filtered_ips = list(self.remove_ignored_ips(ips))

            request.headers["X-Forwarded-For"] = (
                filtered_ips[-1] if filtered_ips else ""
            )
        return self.handler(request)

    def remove_ignored_ips(self, ips):
        """Remove ignored IPs from the list."""
        for ip in ips:
            is_ignored = any(
                [IPv4Address(ip) in network for network in self.ignored_ip_networks]
            )
            if not is_ignored:
                yield ip

    def get_cloudflare_ip_networks(self):
        """Get the list of Cloudflare's current IP ranges."""
        try:
            res = requests.get("https://www.cloudflare.com/ips-v4", timeout=10)
            res.raise_for_status()
            return [IPv4Network(n) for n in res.text.split()]
        except Exception as e:
            if self.registry.settings.get("pyramid_heroku.structlog"):
                import structlog

                logger = structlog.getLogger(__name__)
            else:

                logger = logging.getLogger(__name__)
            logger.exception("Failed getting a list of Cloudflare IPs", exc_info=e)

            return []
