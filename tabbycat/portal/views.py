import json
import logging
import time

import stripe
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django_tenants.utils import schema_context

from notifications.models import EmailStatus, SentMessage
from utils.mixins import AssistantMixin
from utils.tables import BaseTableBuilder
from utils.views import PostOnlyRedirectView, VueTableTemplateView

from .forms import InstanceCreationForm, UserCreationForm
from .models import Client

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_instance_url(request, instance):
    link = request.scheme + "://" + instance.domain
    server_port = request.META.get('SERVER_PORT', 443)
    if server_port != 443 and server_port != 80 and server_port != 8000:
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
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('stripe-payment-redirect', kwargs={'schema': self.object.schema_name})


class StripeSessionView(AssistantMixin, View):

    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        client = get_object_or_404(Client, user=request.user, pk=body['client_id'])
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': settings.INSTANCE_PRICE_ID,
                'quantity': 1,
                'description': client.name,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('successful-payment', kwargs={'schema': client.schema_name}),
            ) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('cancelled-payment')),
        )
        client.session_id = session['id']
        client.payment_id = session['payment_intent']
        client.save()
        return JsonResponse({'sessionId': session['id']}, status=201)


class StripeRedirectView(AssistantMixin, TemplateView):
    template_name = 'square_redirect.html'

    def get(self, request, *args, **kwargs):
        self.client = Client.objects.get(schema_name=self.kwargs['schema'])
        if self.client.paid > 1000:  # Some number, but redirect if already paid
            return HttpResponseRedirect(get_instance_url(request, self.client.get_primary_domain()))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['client'] = self.client
        kwargs['stripe_public_key'] = settings.STRIPE_PUBLISH_KEY
        return kwargs


class StripeWebhookView(View):

    def post(self, request, *args, **kwargs):
        signature = request.META['HTTP_STRIPE_SIGNATURE']
        logger.info(signature)

        try:
            event = stripe.Webhook.construct_event(request.body, signature, settings.STRIPE_ENDPOINT_SEC)
        except ValueError:  # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:  # Invalid signature
            return HttpResponse(status=400)

        actions = {
            'payment_intent.succeeded': self.on_payment_success,
            'payment_intent.canceled': self.on_payment_deny,
            'payment_intent.payment_failed': self.on_payment_deny,
        }
        actions[event['type']](event['data']['object'])

        return HttpResponse(status=200)

    def on_payment_success(self, payment):
        client = get_object_or_404(Client, payment_id=payment['id'])
        client.paid = payment.get('amount', 0)
        client.save()

        # Create schema
        async_to_sync(get_channel_layer().send)("portal", {
            "type": "create_schema",
            "client": client.id,
        })

    def on_payment_deny(self, payment):
        client = get_object_or_404(Client, payment_id=payment['id'])
        client.delete()


class CancelledPaymentRedirectView(View):
    redirect_url = reverse_lazy('create-instance')

    def get(self, request, *args, **kwargs):
        messages.error(self.request, _("The payment was cancelled."))
        return HttpResponseRedirect(self.redirect_url)


class SuccessfulPaymentLandingView(View):

    def get(self, request, *args, **kwargs):
        client = Client.objects.get(schema_name=self.kwargs['schema'])
        time.sleep(5)  # Wait a few seconds to finish making the schema
        return HttpResponseRedirect(get_instance_url(request, client.get_primary_domain()))


class SESWebhookView(View):

    def post(self, request, *args, **kwargs):
        if kwargs['wh_key'] != settings.SES_WEBHOOK_KEY:
            return HttpResponse(status=403)
        body = json.loads(request.body)

        status = None
        if body.get('bounce') is not None:
            status = EmailStatus.EVENT_TYPE_BOUNCED
        elif body.get('complaint') is not None:
            status = EmailStatus.EVENT_TYPE_SPAM
        elif body.get('delivery') is not None:
            status = EmailStatus.EVENT_TYPE_DELIVERED

        headers = {h['name']: h['value'] for h in body.get('headers', {})}
        with schema_context(headers.get('X-TCSITE')):
            message = SentMessage.objects.get(hook_id=headers.get('X-HOOKID'))
            message.emailstatus_set.create(event=status)

        return HttpResponse(status=200)
