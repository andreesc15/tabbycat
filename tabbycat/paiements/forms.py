import datetime

from django import forms

from participants.models import Institution

from .models import Payment


class AdhesionPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('institution',)

    def get_paid_institutions(self):
        today = datetime.date.today()
        annee = datetime.date(today.year, 8, 1) if today.month > 8 \
            else datetime.date(today.year - 1, 8, 1)
        return Payment.objects.filter(
            date__gt=annee, tournament__isnull=True, statut=Payment.STATUT_TERMINE
        ).values_list('institution_id', flat=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institution'].queryset = Institution.objects.exclude(
            id__in=self.get_paid_institutions()
        )


class PublicParticipantSelectForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ()


class AdminPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('methode',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['methode'].choices = Payment.ADMIN_METHODE_CHOICES
