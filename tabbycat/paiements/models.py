from django.db import models


class Payment(models.Model):

	METHODE_ENLIGNE = 'o'
	METHODE_CARTE = 'c'
	METHODE_COMPTANT = 'p'
	METHODE_CHOICES = (
		(METHODE_ENLIGNE, 'En ligne'),
		(METHODE_CARTE, 'Par crédit'),
		(METHODE_COMPTANT, 'En comptant'),
	)

	STATUT_TERMINE = 'f'
	STATUT_OUVERT = 'o'
	STATUT_ANNULE = 'a'
	STATUT_CHOICES = (
		(STATUT_TERMINE, 'Payé'),
		(STATUT_OUVERT, 'Ouvert'),
		(STATUT_ANNULE, 'Annulé'),
	)

	date = models.DateTimeField(auto_now=True)
	reference = models.CharField(editable=False, max_length=40, unique=True,
		verbose_name='reference')
	order = models.CharField(max_length=30, unique=True, blank=True, null=True)

	tournoi = models.ForeignKey('tournaments.Tournament', models.SET_NULL,
		blank=True, null=True, verbose_name='tournoi')
	ecole = models.ForeignKey('participants.Institution', models.SET_NULL,
		blank=True, null=True, verbose_name='école')

	personnes = models.ManyToManyField('participants.Person',
		verbose_name='personnes')

	methode = models.CharField(max_length=1, choices=METHODE_CHOICES)
	statut = models.CharField(max_length=1, choices=STATUT_CHOICES)

	@property
	def isAdhesion(self):
		return self.tournoi is None

	@property
	def numJuges(self):
		return self.personnes.filter(adjudicator__isnull=False).count()

	@property
	def numDebatteurs(self):
		return self.personnes.filter(speaker__isnull=False).count()
