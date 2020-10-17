from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin, TenantMixin
from pytz import common_timezones


class Client(TenantMixin):
    user = models.ForeignKey(get_user_model(), models.PROTECT, blank=True, null=True)
    name = models.CharField(max_length=100,
        verbose_name=_("name"),
        help_text=_("The name for the site that will appear in the list of your sites."))
    archive = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)

    paid = models.IntegerField(default=0)  # In cents
    session_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    timezone = models.CharField(
        max_length=len(max(common_timezones, key=len)),
        choices=((t, t) for t in common_timezones),
        default='Australia/Melbourne',  # From settings.TIME_ZONE
        verbose_name=_("time zone"))

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = False
    auto_drop_schema = True

    def __str__(self):
        return "%s (%s)" % (self.name, self.schema_name)


class Instance(DomainMixin):
    pass
