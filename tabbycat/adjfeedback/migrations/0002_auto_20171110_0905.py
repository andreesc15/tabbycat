# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-10 09:05
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('participants', '0001_initial'),
        ('tournaments', '0001_initial'),
        ('adjfeedback', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('adjallocation', '0002_debateadjudicator_adjudicator'),
    ]

    operations = [
        migrations.AddField(
            model_name='adjudicatortestscorehistory',
            name='adjudicator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='participants.Adjudicator', verbose_name='adjudicator'),
        ),
        migrations.AddField(
            model_name='adjudicatortestscorehistory',
            name='round',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournaments.Round', verbose_name='round'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackstringanswer',
            name='feedback',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedback', verbose_name='feedback'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackstringanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedbackQuestion', verbose_name='question'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackquestion',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tournaments.Tournament', verbose_name='tournament'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackintegeranswer',
            name='feedback',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedback', verbose_name='feedback'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackintegeranswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedbackQuestion', verbose_name='question'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackfloatanswer',
            name='feedback',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedback', verbose_name='feedback'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackfloatanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedbackQuestion', verbose_name='question'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackbooleananswer',
            name='feedback',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedback', verbose_name='feedback'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedbackbooleananswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='adjfeedback.AdjudicatorFeedbackQuestion', verbose_name='question'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedback',
            name='adjudicator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='participants.Adjudicator', verbose_name='adjudicator'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedback',
            name='confirmer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='adjfeedback_adjudicatorfeedback_confirmed', to=settings.AUTH_USER_MODEL, verbose_name='confirmer'),
        ),
        migrations.AddField(
            model_name='adjudicatorfeedback',
            name='source_adjudicator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='adjallocation.DebateAdjudicator', verbose_name='source adjudicator'),
        ),
    ]
