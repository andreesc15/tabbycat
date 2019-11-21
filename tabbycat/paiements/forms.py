from django import forms

from .models import Payment


class AdhesionPaymentForm(forms.ModelForm):

	class Meta:
		model = Payment
		fields = ('ecole',)
