from django.db import models

from participants.models import Person


class Juge(Person):
    tournament = models.ForeignKey('tournaments.Tournament', models.CASCADE)


class Orateur(Person):
    tournament = models.ForeignKey('tournaments.Tournament', models.CASCADE)


class Joute(models.Model):
    tournament = models.ForeignKey('tournaments.Tournament', models.CASCADE)
    seq = models.IntegerField()

    start_time = models.TimeField(null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return "Ronde %d" % self.seq

    @property
    def finaux(self):
        return not self.objects.filter(tournament=self.tournament, seq__gt=self.seq).exists()


class Salle(models.Model):
    joute = models.ForeignKey(Joute, models.CASCADE)
    venue = models.ForeignKey('venues.Venue', models.SET_NULL, blank=True, null=True)

    juges = models.ManyToManyField(Juge)
    orateurs = models.ManyToManyField(Orateur, through='OrateurSalle')

    def __str__(self):
        return "%s @ %s" % (self.joute, self.venue)


class OrateurSalle(models.Model):
    orateur = models.ForeignKey(Orateur, models.CASCADE)
    salle = models.ForeignKey(Salle, models.CASCADE)

    points = models.PositiveIntegerField(blank=True, null=True,
        help_text='0 points en dernier place')
