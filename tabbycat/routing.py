import logging
import re

from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.db import connection

from actionlog.consumers import ActionLogEntryConsumer
from adjallocation.consumers import AdjudicatorAllocationWorkerConsumer, PanelEditConsumer
from checkins.consumers import CheckInEventConsumer
from draw.consumers import DebateEditConsumer
from notifications.consumers import NotificationQueueConsumer
from portal.consumers import PortalQueueConsumer
from results.consumers import BallotResultConsumer, BallotStatusConsumer
from venues.consumers import VenuesWorkerConsumer

logger = logging.getLogger("django.channels.server")


class TenantSchemaMiddleware:
    """Switch schema to the tenant's schema."""

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        for name, value in scope.get("headers", []):
            logger.info("WSS header: %(name)s -> %(value)s", {"name": name.decode("ascii"), "value": value.decode("ascii")})
            if name == b"host":
                schema = value.decode("ascii").split(".")[0]
                assert bool(re.compile(r'^[_a-zA-Z0-9]{1,63}$').match(schema)) and schema[:3] != "pg_", "Must be valid schema"
                scope['schema'] = schema
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path to %s, public;", [schema])
                break
        else:
            raise KeyError("Host is not in headers")

        with connection.cursor() as cursor:
            cursor.execute("SHOW search_path;")
            logger.info("Search path is now %(path)s", {"path": cursor.fetchone()})

        return self.inner(scope)


# This acts like a urls.py equivalent; need to import the channel routes
# from sub apps into this file (plus specifying their top level URL path)
# Note the lack of trailing "/" (but paths in apps need a trailing "/")

application = ProtocolTypeRouter({

    # HTTP handled automatically

    # WebSocket handlers
    "websocket": TenantSchemaMiddleware(AuthMiddlewareStack(
        URLRouter([
            # TournamentOverviewContainer
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/action_logs/$', ActionLogEntryConsumer),
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/ballot_results/$', BallotResultConsumer),
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/ballot_statuses/$', BallotStatusConsumer),
            # CheckInStatusContainer
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/checkins/$', CheckInEventConsumer),
            # Draw and Preformed Panel Edits
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/round/(?P<round_seq>[-\w_]+)/debates/$', DebateEditConsumer),
            url(r'^ws/(?P<tournament_slug>[-\w_]+)/round/(?P<round_seq>[-\w_]+)/panels/$', PanelEditConsumer),
        ]),
    )),

    # Worker handlers (which don't need a URL/protocol)
    "channel": ChannelNameRouter({
        # Name used in runworker cmd : SyncConsumer responsible
        "notifications":  NotificationQueueConsumer, # Email sending
        "portal": PortalQueueConsumer,  # For creating schemas
        "adjallocation": AdjudicatorAllocationWorkerConsumer,
        "venues": VenuesWorkerConsumer,
    }),
})
