from django.db.models import Q

from rest_framework import serializers

from breakqual.models import BreakCategory
from participants.emoji import pick_unused_emoji
from participants.models import Adjudicator, Speaker, SpeakerCategory, Team
from tournaments.models import Tournament

from .fields import TournamentHyperlinkedIdentityField


class TournamentSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField(
        view_name='api-tournament-detail',
        lookup_field='slug', lookup_url_kwarg='tournament_slug')

    class TournamentLinksSerializer(serializers.Serializer):
        break_categories = serializers.HyperlinkedIdentityField(
            view_name='api-breakcategory-list',
            lookup_field='slug', lookup_url_kwarg='tournament_slug')
        speaker_categories = serializers.HyperlinkedIdentityField(
            view_name='api-speakercategory-list',
            lookup_field='slug', lookup_url_kwarg='tournament_slug')

    _links = TournamentLinksSerializer(source='*', read_only=True)

    class Meta:
        model = Tournament
        fields = ('name', 'short_name', 'slug', 'seq', 'active', 'url', '_links')


class BreakCategorySerializer(serializers.ModelSerializer):

    class BreakCategoryLinksSerializer(serializers.Serializer):
        eligibility = TournamentHyperlinkedIdentityField(
            view_name='api-breakcategory-eligibility', lookup_field='slug')

    url = TournamentHyperlinkedIdentityField(
        view_name='api-breakcategory-detail', lookup_field='slug')
    _links = BreakCategoryLinksSerializer(source='*', read_only=True)

    class Meta:
        model = BreakCategory
        fields = ('name', 'slug', 'seq', 'break_size', 'is_general', 'priority',
                  'limit', 'rule', 'url', '_links')


class SpeakerCategorySerializer(serializers.ModelSerializer):

    class SpeakerCategoryLinksSerializer(serializers.Serializer):
        eligibility = TournamentHyperlinkedIdentityField(
            view_name='api-speakercategory-eligibility', lookup_field='slug')

    url = TournamentHyperlinkedIdentityField(
        view_name='api-speakercategory-detail', lookup_field='slug')
    _links = SpeakerCategoryLinksSerializer(source='*', read_only=True)

    class Meta:
        model = SpeakerCategory
        fields = ('name', 'slug', 'seq', 'limit', 'public', 'url', '_links')


class BreakEligibilitySerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team_set'] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=kwargs['context']['tournament'].team_set.all()
        )

    class Meta:
        model = BreakCategory
        fields = ('slug', 'team_set')

    def update(self, instance, validated_data):
        teams = validated_data['team_set']

        if self.partial:
            # Add teams to category, don't remove any
            self.instance.team_set.add(*teams)
        else:
            self.instance.team_set.set(teams)
        return self.instance


class SpeakerEligibilitySerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker_set'] = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=Speaker.objects.filter(team__tournament=kwargs['context']['tournament'])
        )

    class Meta:
        model = SpeakerCategory
        fields = ('slug', 'speaker_set')

    def update(self, instance, validated_data):
        speakers = validated_data['speaker_set']

        if self.partial:
            # Add speakers to category, don't remove any
            self.instance.speaker_set.add(*speakers)
        else:
            self.instance.speaker_set.set(speakers)
        return self.instance


class SpeakerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categories'] = serializers.SlugRelatedField(
            many=True,
            queryset=kwargs['context']['tournament'].speakercategory_set.all(),
            slug_field="slug"
        )

    class Meta:
        model = Speaker
        fields = ('id', 'name', 'gender', 'email', 'categories')


class AdjudicatorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Adjudicator
        fields = ('id', 'name', 'gender', 'email', 'institution', 'base_score',
                  'trainee', 'independent', 'adj_core')

    def create(self, validated_data):
        adj = super().create(validated_data)

        if adj.institution is not None:
            adj.adjudicatorinstitutionconflict_set.create(institution=adj.institution)

        return adj


class TeamSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    emoji = serializers.CharField(
        required=False, max_length=2,
        help_text='Automatically generated if not specified. Do not include variation selectors or modifiers.'
    )  # Remove choices list

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['break_categories'] = serializers.SlugRelatedField(
            many=True,
            queryset=kwargs['context']['tournament'].breakcategory_set.all(),
            slug_field="slug"
        )
        self.fields['speakers'] = SpeakerSerializer(
            many=True,
            context=kwargs['context']
        )

    class Meta:
        model = Team
        fields = ('id', 'reference', 'code_name', 'emoji', 'institution', 'speakers',
                  'use_institution_prefix', 'break_categories')

    def create(self, validated_data):
        """Four things must be done, excluding saving the Team object:
        1. Create the short_reference based on 'reference',
        2. Create emoji/code name if not stated,
        3. Create the speakers.
        4. Add institution conflict"""
        validated_data['short_reference'] = validated_data['reference'][:34]
        speakers_data = validated_data.pop('speakers')
        break_categories = validated_data.pop('break_categories')

        emoji, code_name = pick_unused_emoji()
        if 'emoji' not in validated_data:
            validated_data['emoji'] = emoji
        if 'code_name' not in validated_data:
            validated_data['code_name'] = code_name

        team = Team.objects.create(**validated_data)
        team.break_categories.set(team.tournament.breakcategory_set.filter(
            Q(is_general=True) | Q(name__in=break_categories)
        ))

        speakers = SpeakerSerializer(many=True, data=speakers_data, context={'tournament': team.tournament})
        if speakers.is_valid():
            speakers.save(team=team)

        if team.institution is not None:
            team.teaminstitutionconflict_set.create(institution=team.institution)

        return team
