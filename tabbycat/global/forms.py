from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Client, Instance


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
        exclude = ('user', 'paid')

    def save(self, commit=True):
        client = super().save(commit=False)
        client.user = self.user

        if commit:
            client.save()

            main_instance = Instance.objects.get(tenant__schema_name='public')
            Instance.objects.create(tenant=client, domain=client.schema_name + "." + main_instance.domain)

        return client
