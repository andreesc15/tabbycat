from django.db import models


class Payment(models.Model):

    METHODE_ENLIGNE = 'o'
    METHODE_CARTE = 'c'
    METHODE_COMPTANT = 'p'
    METHODE_VOID = 'v'
    METHODE_CHOICES = (
        (METHODE_ENLIGNE, 'En ligne'),
        (METHODE_CARTE, 'Par crédit'),
        (METHODE_COMPTANT, 'En comptant'),
        (METHODE_VOID, 'Void'),
    )
    ADMIN_METHODE_CHOICES = (
        (METHODE_CARTE, 'Par crédit'),
        (METHODE_COMPTANT, 'En comptant'),
        (METHODE_VOID, 'Void'),
    )

    STATUT_TERMINE = 'f'
    STATUT_OUVERT = 'o'
    STATUT_ANNULE = 'a'
    STATUT_ECHOUE = 'e'
    STATUT_CHOICES = (
        (STATUT_TERMINE, 'Payé'),
        (STATUT_OUVERT, 'Ouvert'),
        (STATUT_ANNULE, 'Annulé'),
        (STATUT_ECHOUE, 'Échoué'),
    )

    date = models.DateTimeField(auto_now=True)
    reference = models.CharField(editable=False, max_length=40, unique=True,
        verbose_name='reference')

    checkout = models.CharField(max_length=30, unique=True, blank=True, null=True)
    order = models.CharField(max_length=64, unique=True, blank=True, null=True)

    tournament = models.ForeignKey('tournaments.Tournament', models.SET_NULL,
        blank=True, null=True, verbose_name='tournament')
    institution = models.ForeignKey('participants.Institution', models.SET_NULL,
        blank=True, null=True, verbose_name='école')

    personnes = models.ManyToManyField('participants.Person',
        verbose_name='personnes')

    methode = models.CharField(max_length=1, choices=METHODE_CHOICES)
    statut = models.CharField(max_length=1, choices=STATUT_CHOICES)

    def __str__(self):
        return self.reference

    @property
    def isAdhesion(self):
        return self.tournament is None

    @property
    def numJuges(self):
        return self.personnes.filter(adjudicator__isnull=False).count()

    @property
    def numDebatteurs(self):
        return self.personnes.filter(speaker__isnull=False).count()

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._construct_reference()
        super().save(*args, **kwargs)

    def _construct_reference(self):
        import string
        from utils.misc import generate_identifier_string

        institution = 'SO' if self.institution is None else self.institution.code
        event = 'adhesion' if self.tournament is None else self.tournament.slug
        reference = event + '/' + institution + '/' + generate_identifier_string(string.digits, 40)
        return reference[:40]
