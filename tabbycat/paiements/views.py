import datetime

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from django.views.generic.edit import FormView

from participants.models import Adjudicator, Institution, Person, Speaker
from settings.core import ADHESION_AMOUNT
from tournaments.mixins import TournamentMixin
from tournaments.models import Tournament
from utils.misc import reverse_tournament
from utils.mixins import AdministratorMixin
from utils.views import PostOnlyRedirectView, VueTableTemplateView
from utils.tables import BaseTableBuilder, TabbycatTableBuilder

from .forms import AdhesionPaymentForm, AdminPaymentForm, PublicParticipantSelectForm
from .models import Payment
from .square import create_payment
from .utils import update_or_create_payments


class PublicAdhesionPaymentView(FormView):
    template_name = 'public_subscription.html'
    form_class = AdhesionPaymentForm

    def form_valid(self, form):
        paiement = Payment(
            institution=form.cleaned_data['institution'], montant=ADHESION_AMOUNT,
            methode=Payment.METHODE_ENLIGNE, statut=Payment.STATUT_OUVERT,
        )
        paiement.save()

        return_url = self.request.build_absolute_uri(reverse('paiements-return'))
        square_response = create_payment(paiement, return_url)

        return HttpResponseRedirect(square_response['checkout']['checkout_page_url'])


class PaymentReturnView(View):

    def get(self, request, *args, **kwargs):
        paiement = Payment.objects.get(reference=request.GET.get('referenceId'))
        paiement.order = request.GET.get('transactionId')
        paiement.save()

        messages.success(request, "Votre paiement a été reçu !")
        update_or_create_payments()  # Update the listing as soon as possible
        return HttpResponseRedirect(reverse('tabbycat-index'))


class PaymentRefreshView(AdministratorMixin, PostOnlyRedirectView):

    redirect_url = reverse_lazy('paiements-adhesion-admin')

    def post(self, request, *args, **kwargs):
        update_or_create_payments()
        return super().post(request, *args, **kwargs)


class AdminAdhesionPaymentView(AdministratorMixin, VueTableTemplateView, FormView):
    template_name = "select_payments.html"
    page_title = "Paiements d'adhésion"
    page_emoji = '💰'
    success_url = reverse_lazy('paiements-adhesion-admin')
    view_role = ""

    form_class = AdminPaymentForm

    def setup(self, request, *args, **kwargs):
        today = datetime.date.today()
        annee = datetime.date(today.year, 8, 1) if today.month > 8 \
            else datetime.date(today.year - 1, 8, 1)
        self.deja_paye = Payment.objects.filter(
            date__gt=annee, tournament__isnull=True, statut=Payment.STATUT_TERMINE
        ).values_list('institution_id', flat=True)
        return super().setup(request, *args, **kwargs)

    def _ecole_class(self, p):
        style = 'no-wrap' if len(p.name) < 20 else ''
        style += ' text-muted' if p.id in self.deja_paye else ''
        return style

    def get_table(self):
        table = BaseTableBuilder(title="Adhésion d'école", sort_key='payer')

        queryset = Institution.objects.all()
        table.add_column({'key': 'payer', 'title': "Payer l'adhésion"}, [{
            'component': 'check-cell',
            'checked': p.id in self.deja_paye,
            'id': p.id,
            'name': 'institution',
            'value': p.id,
            'noSave': True,
        } for p in queryset])

        table.add_column({'key': 'name', 'tooltip': 'École', 'icon': 'home'}, [{
            'text': p.name,
            'class': self._ecole_class(p)
        } for p in queryset])

        return table

    def post(self, request, *args, **kwargs):
        insts = Institution.objects.filter(
            id__in=list(map(int, request.POST.getlist('institution'))),
        ).exclude(id__in=self.deja_paye)

        for inst in insts:
            paiement = Payment(
                institution=inst, methode=request.POST.get('methode'),
                statut=Payment.STATUT_TERMINE, montant=ADHESION_AMOUNT
            )
            paiement.save()

        messages.success(request, "Les paiement d'adhésion ont été reçus !")

        return super().post(request, *args, **kwargs)


class PublicPaymentInstitutionView(TournamentMixin, VueTableTemplateView):
    page_title = "Paiements de tournoi"
    page_emoji = '💰'

    def get_table(self):
        table = TabbycatTableBuilder(view=self, title='Selectionner un école', sort_key='name')

        queryset = Institution.objects.all().order_by('name')

        table.add_column({'key': 'name', 'tooltip': 'École', 'icon': 'home'}, [{
            'text': p.name,
            'link': reverse_tournament('paiements-tournament-add', self.tournament, kwargs={'institution_id': p.pk}),
            'class': 'no-wrap' if len(p.name) < 20 else ''
        } for p in queryset])

        return table


class AdminPaymentView(AdministratorMixin, TournamentMixin, VueTableTemplateView):
    template_name = "admin_payments.html"
    page_title = "Paiements de tournoi"
    page_emoji = '💰'

    def _institution_name(self, p):
        inst = None
        if hasattr(p, 'adjudicator'):
            inst = p.adjudicator.institution
        if hasattr(p, 'speaker'):
            inst = p.speaker.team.institution
        if inst is not None:
            inst = inst.code
        return inst

    def get_tables(self):
        self.paiements = Payment.objects.filter(tournament=self.tournament).values_list('pk', flat=True)
        return [self.get_summary_table(), self.get_paid_table(), self.get_unpaid_table()]

    def get_summary_table(self):

        table = TabbycatTableBuilder(
            view=self,
            title='Sommaire',
            sort_key='institution'
        )

        institutions = Institution.objects.filter(
            Q(team__tournament=self.tournament) | Q(adjudicator__tournament=self.tournament)
        ).distinct().annotate(
            num_paye_juges=Count('adjudicator', filter=Q(adjudicator__payment__in=self.paiements), distinct=True),
            num_paye_deb=Count('team__speaker', filter=Q(team__speaker__payment__in=self.paiements), distinct=True),
            num_nonpaye_juges=Count('adjudicator',
                filter=~Q(adjudicator__payment__in=self.paiements) & Q(adjudicator__tournament=self.tournament), distinct=True),
            num_nonpaye_deb=Count('team__speaker',
                filter=~Q(team__speaker__payment__in=self.paiements) & Q(team__tournament=self.tournament), distinct=True),
        )

        table.add_column({'key': 'institution', 'tooltip': "École", 'icon': 'home'}, [{
            'text': i.name
        } for i in institutions])

        table.add_column({'key': 'paye', 'title': "Payé"}, [{
            'text': str(i.num_paye_deb) + "/" + str(i.num_paye_juges)
        } for i in institutions])

        table.add_column({'key': 'nonpaye', 'title': "Non-Payé"}, [{
            'text': str(i.num_nonpaye_deb) + "/" + str(i.num_nonpaye_juges)
        } for i in institutions])

        return table

    def get_payment_table(self, title, participants):

        table = TabbycatTableBuilder(
            view=self,
            title=title,
            sort_key='institution'
        )

        table.add_column({'key': 'name', 'tooltip': "Participants", 'icon': 'user'}, [{
            'text': p.name
        } for p in participants])

        table.add_column({'key': 'role', 'title': 'Rôle'}, [{
            'text': 'Juge' if hasattr(p, 'adjudicator') else 'Débatteur'
        } for p in participants])

        table.add_column({'key': 'institution', 'tooltip': "École", 'icon': 'home'}, [{
            'text': 'S/O' if self._institution_name(p) is None else self._institution_name(p),
            'class': 'text-muted' if self._institution_name(p) is None else ''
        } for p in participants])

        return table

    def get_paid_table(self):
        participants = Person.objects.filter(payment__in=self.paiements).distinct().select_related(
            'adjudicator', 'adjudicator__institution',
            'speaker', 'speaker__team', 'speaker__team__institution',
        )
        return self.get_payment_table('Payé', participants)

    def get_unpaid_table(self):
        dans_tournoi = Q(speaker__team__tournament=self.tournament) | Q(adjudicator__tournament=self.tournament)
        participants = Person.objects.filter(
             ~Q(payment__in=self.paiements) & dans_tournoi
        ).distinct().select_related(
            'adjudicator', 'adjudicator__institution',
            'speaker', 'speaker__team', 'speaker__team__institution',
        )
        return self.get_payment_table('Non-Payé', participants)


class BasePaymentSelectView(TournamentMixin, VueTableTemplateView, FormView):
    page_emoji = '💰'
    template_name = "select_payments.html"

    def _person_style(self, person):
        style = 'no-wrap ' if len(person.name) < 20 else ''
        style += 'text-muted' if person.pk in self.deja_paye else ''
        return style

    def get_speaker_queryset(self):
        filters = Q(team__tournament=self.tournament, team__institution=self.institution)
        filters |= Q(team__tournament=self.tournament, team__institution__isnull=True)
        return Speaker.objects.filter(filters)

    def get_adjudicator_queryset(self):
        filters = Q(tournament=self.tournament, institution=self.institution)
        filters |= Q(tournament=self.tournament, institution__isnull=True)
        return Adjudicator.objects.filter(filters)

    def get_tables(self):
        if self.kwargs.get('institution_id') is None:
            self.institution = Institution.objects.none()
        else:
            self.institution = Institution.objects.get(pk=self.kwargs['institution_id'])
        self.deja_paye = Payment.personnes.through.objects.filter(
            payment__tournament=self.tournament, payment__statut=Payment.STATUT_TERMINE,
        ).values_list('person_id', flat=True)

        return [self.get_speaker_table(), self.get_adjudicator_table()]

    def get_table(self, title, people):
        table = TabbycatTableBuilder(
            view=self,
            title=title,
            sort_key='name'
        )

        table.add_column({'key': 'payer', 'title': 'Payer'}, [{
            'component': 'check-cell',
            'checked': False,
            'id': p.id,
            'name': 'personnes',
            'value': p.id,
            'noSave': True
        } for p in people])

        table.add_column({'key': 'name', 'tooltip': "Participant", 'icon': 'user'}, [{
            'text': p.name,
            'class': self._person_style(p)
        } for p in people])

        self.add_extra_columns(table, people)

        return table

    def get_speaker_table(self):
        speakers = self.get_speaker_queryset()
        return self.get_table('Débatteurs', speakers)

    def get_adjudicator_table(self):
        adjs = self.get_adjudicator_queryset()
        return self.get_table('Juges', adjs)


class PublicPaymentSelectView(BasePaymentSelectView):
    form_class = PublicParticipantSelectForm

    def get_page_title(self):
        self.institution = Institution.objects.get(pk=self.kwargs['institution_id'])
        return 'Paiements de participant (%s)' % self.institution.name

    def add_extra_columns(self, table, people):
        pass

    def post(self, request, *args, **kwargs):
        institution = Institution.objects.get(pk=self.kwargs['institution_id'])
        personnes = Person.objects.filter(id__in=list(map(int, request.POST.getlist('personnes'))))
        paiement = Payment(
            institution=institution, tournament=self.tournament,
            methode=Payment.METHODE_ENLIGNE, statut=Payment.STATUT_OUVERT,
        )
        paiement.save()
        paiement.personnes.add(*personnes)
        paiement.set_montant()

        return_url = request.build_absolute_uri(reverse('paiements-return'))
        square_response = create_payment(paiement, return_url)

        return HttpResponseRedirect(square_response['checkout']['checkout_page_url'])


class AdminPaymentSelectView(AdministratorMixin, BasePaymentSelectView):
    page_title = "Payer inscription"
    form_class = AdminPaymentForm

    def get_success_url(self, *args, **kwargs):
        return reverse_tournament('paiements-tournament-add-admin', self.tournament)

    def get_table_title(self):
        return 'Selectionner participants'

    def get_speaker_queryset(self):
        return Speaker.objects.filter(team__tournament=self.tournament).select_related('team', 'team__institution')

    def get_adjudicator_queryset(self):
        return Adjudicator.objects.filter(tournament=self.tournament).select_related('institution')

    def _institution_name(self, p):
        inst = None
        if isinstance(p, Adjudicator):
            inst = p.institution
        if isinstance(p, Speaker):
            inst = p.team.institution
        if inst is not None:
            inst = inst.code
        return inst

    def add_extra_columns(self, table, people):
        table.add_column({'key': 'institution', 'tooltip': 'École', 'icon': 'home'}, [{
            'text': "S/O" if self._institution_name(p) is None else self._institution_name(p),
            'class': 'text-muted' if self._institution_name(p) is None else '',
        } for p in people])

    def post(self, request, *args, **kwargs):
        personnes = Person.objects.filter(id__in=list(map(int, request.POST.getlist('personnes'))))
        personnes_id = personnes.values_list('id', flat=True)

        institution = Institution.objects.filter(
            Q(adjudicator__id__in=personnes_id) | Q(team__speaker__id__in=personnes_id)
        ).distinct()
        if institution.count() > 1:
            messages.error(request, "Vous ne pouvez pas combiner des participants de plusieurs écoles.")
            return HttpResponseRedirect(reverse_tournament('paiements-tournament-add-admin', self.tournament))

        paiement = Payment(
            institution=institution.first(), tournament=self.tournament,
            methode=request.POST.get('methode'), statut=Payment.STATUT_TERMINE,
        )
        paiement.save()
        paiement.personnes.add(*personnes)
        paiement.set_montant()

        return super().post(request, *args, **kwargs)
