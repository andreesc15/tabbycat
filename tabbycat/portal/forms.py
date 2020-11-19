from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Client


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        fields = ("username", "email")
        labels = {"email": _("E-mail address")}


class InstanceCreationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Client
        fields = ("name", "schema_name")
        labels = {
            "schema_name": _("Slug"),
            "name": _("Name"),
        }
        help_texts = {
            "schema_name": _("The name used in the URL of the site. Must be alphanumeric."),
            "name": _("The name for the site that will appear in the list of your sites."),
        }

    def save(self, commit=True):
        client = super().save(commit=False)
        client.user = self.user

        if commit:
            client.save()

            # Create schema
            async_to_sync(get_channel_layer().send)("portal", {
                "type": "create_schema",
                "client": client.id,
            })

        return client
