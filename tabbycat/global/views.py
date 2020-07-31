from django.contrib import messages
from django.contrib.auth import login
from django.db import connection
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django_tenants.utils import schema_context

from utils.mixins import AssistantMixin
from utils.tables import BaseTableBuilder
from utils.views import PostOnlyRedirectView, VueTableTemplateView

from .forms import InstanceCreationForm, UserCreationForm
from .models import Client


def get_instance_url(request, instance):
    link = request.scheme + "://" + instance.domain
    server_port = request.META.get('SERVER_PORT', 443)
    if server_port != 443 and server_port != 80:
        link += ":" + str(server_port)
    return link + "/"


class CreateAccountView(FormView):
    template_name = 'registration/create_account.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('notifications-test-email')
    view_role = ""

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.info(self.request, _("Welcome! You've created an account for %s.") % user.username)

        return super().form_valid(form)


class MainPageView(TemplateView):
    template_name = 'main_page.html'
    view_role = "public"


class ListOwnTournamentsView(AssistantMixin, VueTableTemplateView):
    template_name = 'tournaments_list.html'
    page_title = gettext_lazy("Your Tabbycat Sites")

    def get_table(self):
        clients = Client.objects.filter(user=self.request.user)
        table = BaseTableBuilder(view=self, sort_key="date")
        table.add_column(
            {'key': 'name', 'title': _("Site Name")},
            [{'text': c.name, 'link': get_instance_url(self.request, c.domains.get())} for c in clients])
        table.add_column(
            {'key': 'date', 'icon': 'clock', 'tooltip': _("When the site was created")},
            [{'text': c.created_on} for c in clients])
        return table


class DeleteInstanceView(AssistantMixin, PostOnlyRedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('own-tournaments-list')

    def post(self, request, *args, **kwargs):
        client = get_object_or_404(Client, user=request.user, schema_name=self.kwargs['schema'])
        name = client.name

        client.delete()
        messages.success(request, _("Deleted the %s site" % name))
        return super().post(request, *args, **kwargs)


class CreateInstanceFormView(AssistantMixin, FormView):
    template_name = 'create_instance_form.html'
    form_class = InstanceCreationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()

        # Copy user to new site
        user_model = self.request.user.__class__
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO " + self.object.schema_name + ".auth_user SELECT * FROM public.auth_user WHERE id=%d" %
                self.request.user.pk)
        with schema_context(self.object.schema_name):
            user_model.objects.filter(pk=self.request.user.pk).update(is_staff=True, is_superuser=True)

        return super().form_valid(form)

    def get_success_url(self):
        return get_instance_url(self.request, self.object.domains.get())
