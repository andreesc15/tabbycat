from django.core.management import call_command
from django_tenants.management.commands import SyncCommon
from django_tenants.utils import get_public_schema_name, get_tenant_model, schema_context, schema_exists


class Command(SyncCommon):
    help = "Updates options in all schemas."

    def handle(self, *args, **options):
        super().handle(*args, **options)
        self.PUBLIC_SCHEMA_NAME = get_public_schema_name()

        if self.sync_tenant:
            if self.schema_name and self.schema_name != self.PUBLIC_SCHEMA_NAME:
                if not schema_exists(self.schema_name, self.options.get('database', None)):
                    raise RuntimeError('Schema "{}" does not exist'.format(
                        self.schema_name))
                else:
                    tenants = [self.schema_name]
            else:
                tenants = get_tenant_model().objects.only(
                    'schema_name').exclude(
                    schema_name=self.PUBLIC_SCHEMA_NAME).values_list(
                    'schema_name', flat=True)

            for tenant in tenants:
                with schema_context(tenant):
                    call_command('checkpreferences')
