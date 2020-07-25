from django.contrib.auth import get_user_model
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    user = models.ForeignKey(get_user_model(), models.PROTECT)
    name = models.CharField(max_length=100)
    paid = models.BooleanField()
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True


class Instance(DomainMixin):
    pass
