from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'reference', 'methode', 'statut')
    list_filter = ('methode', 'statut', 'tournament')
    search_fields = ('tournament','institution')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
                'tournament', 'institution').prefetch_related('personnes')
