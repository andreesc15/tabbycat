from django.views.generic import View
from django.views.generic.edit import FormView

from tournaments.mixins import TournamentMixin
from utils.misc import reverse_tournament
from utils.mixins import AdministratorMixin
from utils.views import PostOnlyRedirectView, VueTableTemplateView
from utils.tables import TabbycatTableBuilder

from .forms import AdhesionPaymentForm


class PublicAdhesionPaymentView(FormView):
	form_class = AdhesionPaymentForm


class PaymentRedirectView(PostOnlyRedirectView):
	pass


class PaymentReturnView(View):
	pass


class AdminAdhesionPaymentView(AdministratorMixin, VueTableTemplateView):
	pass


class AdminAdhesionAddPaymentView(AdministratorMixin, PostOnlyRedirectView):
	pass


class PublicPaymentInstitutionView(TournamentMixin, VueTableTemplateView):
	pass


class PublicPaymentSelectView(TournamentMixin, VueTableTemplateView):
	pass


class AdminPaymentView(AdministratorMixin, VueTableTemplateView):
	pass


class AdminAddPaymentView(AdministratorMixin, FormView):
	pass
