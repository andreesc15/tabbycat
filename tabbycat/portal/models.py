from django.contrib.auth import get_user_model
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    user = models.ForeignKey(get_user_model(), models.PROTECT, blank=True, null=True)
    name = models.CharField(max_length=100)
    archive = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)

    paid = models.IntegerField(default=0)  # In cents
    session_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = False
    auto_drop_schema = True


class Instance(DomainMixin):
    pass
