from django.db import models


class Juge(models.Model):
    person = models.OneToOneField('participants.Person', models.CASCADE)

    def __str__(self):
        return str(self.person)


class Orateur(models.Model):
    person = models.OneToOneField('participants.Person', models.CASCADE)

    def __str__(self):
        return str(self.person)


class Joute(models.Model):
    tournament = models.ForeignKey('tournaments.Tournament', models.CASCADE)
    seq = models.IntegerField()

    start_time = models.TimeField(null=True)
    completed = models.BooleanField(default=False)

    @property
    def name(self):
        return "Ronde %d" % self.seq


class Salle(models.Model):
    joute = models.ForeignKey(Joute, models.CASCADE)
    venue = models.ForeignKey('venues.Venue', models.SET_NULL, blank=True, null=True)

    juges = models.ManyToManyField(Juge)
    orateurs = models.ManyToManyField(Orateur, through='OrateurSalle')


class OrateurSalle(models.Model):
    orateur = models.ForeignKey(Orateur, models.CASCADE)
    salle = models.ForeignKey(Salle, models.CASCADE)

    points = models.PositiveIntegerField(blank=True)
