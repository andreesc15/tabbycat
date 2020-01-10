from django.contrib import admin

from .models import Joute, Juge, Orateur, OrateurSalle, Salle


@admin.register(Juge)
class JugeAdmin(admin.ModelAdmin):
    pass


@admin.register(Orateur)
class OrateurAdmin(admin.ModelAdmin):
    pass


@admin.register(Joute)
class JouteAdmin(admin.ModelAdmin):
    list_display = ('seq', 'tournament', 'start_time')
    list_filter = ('tournament',)


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_filter = ('joute__tournament',)


@admin.register(OrateurSalle)
class OrateurSalleAdmin(admin.ModelAdmin):
    pass
