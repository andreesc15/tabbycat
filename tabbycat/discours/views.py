import json
import logging

from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.base import View

from participants.models import Person
from tournaments.mixins import TournamentMixin
from utils.mixins import AdministratorMixin
from utils.tables import TabbycatTableBuilder
from utils.views import VueTableTemplateView

from .models import Juge, Orateur

logger = logging.getLogger(__name__)


class DiscoursParticipantsView(AdministratorMixin, TournamentMixin, VueTableTemplateView):
    template_name = 'edit_discours_participants.html'
    page_title = "Participants aux discours publics"
    page_emoji = '🍯'

    def get_table(self):
        table = TabbycatTableBuilder(view=self, sort_key='person')
        people = Person.objects.filter(
            Q(adjudicator__tournament=self.tournament) | Q(speaker__team__tournament=self.tournament)
        ).select_related('juge', 'orateur')

        table.add_column({'tooltip': "Participants", 'icon': 'user', 'key': 'person'}, [{
            'text': p.name,
        } for p in people])

        table.add_column({'tooltip': 'Orateur', 'icon': 'mic', 'key': 'orateur'}, [{
            'component': 'check-cell',
            'checked': hasattr(p, 'orateur'),
            'id': p.id,
            'type': 'o'
        } for p in people])

        table.add_column({'tooltip': 'Juge', 'icon': 'edit-2', 'key': 'juge'}, [{
            'component': 'check-cell',
            'checked': hasattr(p, 'juge'),
            'id': p.id,
            'type': 'j'
        } for p in people])

        return table


class UpdateDiscoursParticipantsView(AdministratorMixin, TournamentMixin, View):

    def set_status(self, person, sent_status):
        if sent_status['type'] == 'o':
            self.set_orateur_status(person, sent_status)
        else:
            self.set_juge_status(person, sent_status)

    def set_orateur_status(self, person, sent_status):
        marked = hasattr(person, 'orateur')
        if sent_status['checked'] and not marked:
            Orateur(person=person, tournament=self.tournament).save()
        elif not sent_status['checked'] and marked:
            Orateur.objects.filter(person=person).delete()

    def set_juge_status(self, person, sent_status):
        marked = hasattr(person, 'juge')
        if sent_status['checked'] and not marked:
            Juge(person=person, tournament=self.tournament).save()
        elif not sent_status['checked'] and marked:
            Juge.objects.filter(person=person).delete()

    def post(self, request, *args, **kwargs):
        body = self.request.body.decode('utf-8')
        posted_info = json.loads(body)

        try:
            person_ids = [int(key) for key in posted_info.keys()]
            people = Person.objects.select_related('orateur', 'juge').in_bulk(person_ids)
            for person_id, person in people.items():
                self.set_status(person, posted_info[str(person_id)])
        except:
            message = "Error handling updates"
            logger.exception(message)
            return JsonResponse({'status': 'false', 'message': message}, status=500)

        return JsonResponse(json.dumps(True), safe=False)


class DiscoursIndexView(View):
    pass


class DiscoursDrawView(View):
    pass


class DiscoursCreateRoundView(View):
    pass


class DiscoursResultsView(View):
    pass


class PublicDiscoursDrawView(View):
    pass


class PrivateurlResultsView(View):
    pass


class PrivateurlInscriptionView(View):
    pass
