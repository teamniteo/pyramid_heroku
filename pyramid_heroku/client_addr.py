# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.add_tween('pyramid_heroku.client_addr.ClientAddr')


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

    The tween checks if ``X-Forwarded-For`` is present and if it is, takes
    the last IP in the ``X-Forwarded-For`` list and makes it the only IP
    in the list. This effectively causes pyramid to return this real IP for
    ``request.client_addr``. Read rationale behind why we do this on
    https://github.com/niteoweb/heroku_ips.
    """

    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry

    def __call__(self, request):
        if request.headers.get('X-Forwarded-For'):
            request.headers['X-Forwarded-For'] = \
                request.headers['X-Forwarded-For'].split(',')[-1].strip()
        return self.handler(request)
