"""Email generator functions

These functions assemble the necessary arguments to be parsed in email templates
to be sent to relevant parties. All these functions return a tuple with the first
element being a context dictionary with the available variables to be parsed in
the message. The second element is the Person object. All these functions are
called by NotificationQueueConsumer, which inserts the variables into a message,
using the participant object to fetch their email address and to record.

Objects should be fetched from the database here as it is an asyncronous process,
thus the object itself cannot be passed.
"""

from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from adjallocation.allocation import AdjudicatorAllocation
from options.utils import use_team_code_names
from participants.models import Person
from participants.prefetch import populate_win_counts
from results.result import ConsensusDebateResultWithScores, DebateResult, DebateResultByAdjudicatorWithScores
from results.utils import side_and_position_names


adj_position_names = {
    AdjudicatorAllocation.POSITION_CHAIR: _("the chair"),
    AdjudicatorAllocation.POSITION_ONLY: _("the only"),
    AdjudicatorAllocation.POSITION_PANELLIST: _("a panellist"),
    AdjudicatorAllocation.POSITION_TRAINEE: _("a trainee"),
}


def _assemble_panel(adjs):
    adj_string = []
    for adj, pos in adjs:
        adj_string.append("%s (%s)" % (adj.name, adj_position_names[pos]))

    return ", ".join(adj_string)


def adjudicator_assignment_email_generator(to, url, round):
    emails = []
    draw = round.debate_set_with_prefetches(speakers=False).all()
    use_codes = use_team_code_names(round.tournament, False)

    for debate in draw:
        matchup = debate.matchup_codes if use_codes else debate.matchup
        context = {
            'ROUND': round.name,
            'VENUE': debate.venue.display_name if debate.venue is not None else _("TBA"),
            'PANEL': _assemble_panel(debate.adjudicators.with_positions()),
            'DRAW': matchup,
        }

        for adj, pos in debate.adjudicators.with_positions():
            try:
                to.remove(adj.id)
            except ValueError:
                continue

            context_user = context.copy()
            context_user['USER'] = adj.name
            context_user['POSITION'] = adj_position_names[pos]

            if adj.url_key:
                context_user['URL'] = url + adj.url_key + '/'

            emails.append((context_user, adj))

    return emails


def randomized_url_email_generator(to, url, tournament):
    emails = []

    for instance in tournament.participants:
        try:
            to.remove(instance.id)
        except ValueError:
            continue
        url_ind = url + instance.url_key + '/'

        variables = {'USER': instance.name, 'URL': url_ind, 'KEY': instance.url_key, 'TOURN': str(tournament)}

        emails.append((variables, instance))

    return emails


def ballots_email_generator(to, debate):
    emails = []
    tournament = debate.round.tournament
    results = DebateResult(debate.confirmed_ballot)
    round_name = _("%(tournament)s %(round)s @ %(room)s") % {'tournament': str(tournament),
                                                             'round': debate.round.name, 'room': debate.venue.name}

    use_codes = use_team_code_names(tournament, False)

    def _create_ballot(result, scoresheet):
        ballot = "<ul>"

        for side, (side_name, pos_names) in zip(tournament.sides, side_and_position_names(tournament)):
            side_string = ""
            if tournament.pref('teams_in_debate') == 'bp':
                side_string += _("<li>%(side)s: %(team)s (%(points)d points with %(speaks)s total speaks)")
                points = 4 - scoresheet.rank(side)
            else:
                side_string += _("<li>%(side)s: %(team)s (%(points)s - %(speaks)s total speaks)")
                points = _("Win") if side in scoresheet.winners() else _("Loss")

            ballot += side_string % {
                'side': side_name,
                'team': result.debateteams[side].team.code_name if use_codes else result.debateteams[side].team.short_name,
                'speaks': formats.localize(scoresheet.get_total(side)),
                'points': points,
            }

            ballot += "<ul>"

            for pos, pos_name in zip(tournament.positions, pos_names):
                ballot += _("<li>%(pos)s: %(speaker)s (%(score)s)</li>") % {
                    'pos': pos_name,
                    'speaker': result.get_speaker(side, pos).name,
                    'score': formats.localize(scoresheet.get_score(side, pos)),
                }

            ballot += "</ul></li>"

        ballot += "</ul>"

        return mark_safe(ballot)

    if isinstance(results, DebateResultByAdjudicatorWithScores):
        for (adj, ballot) in results.scoresheets.items():
            if adj.email is None:
                continue

            context = {'DEBATE': round_name, 'USER': adj.name, 'SCORES': _create_ballot(results, ballot)}
            emails.append((context, adj))
    elif isinstance(results, ConsensusDebateResultWithScores):
        context = {'DEBATE': round_name, 'SCORES': _create_ballot(results, results.scoresheet)}

        for adj in debate.debateadjudicator_set.all():
            if adj.adjudicator.email is None:
                continue

            context_user = context.copy()
            context_user['USER'] = adj.adjudicator.name

            emails.append((context_user, adj.adjudicator))

    return emails


def standings_email_generator(to, url, round):
    emails = []
    teams = round.active_teams.prefetch_related('speaker_set')
    populate_win_counts(teams)

    context = {
        'TOURN': str(round.tournament),
        'ROUND': round.name,
        'URL': url if round.tournament.pref('public_team_standings') else "",
    }

    for team in teams:
        context_team = context.copy()
        context_team['POINTS'] = str(team.points_count)
        context_team['TEAM'] = team.short_name

        for speaker in team.speaker_set.all():
            try:
                to.remove(speaker.id)
            except ValueError:
                continue

            context_user = context_team.copy()
            context_user['USER'] = speaker.name

            emails.append((context_user, speaker))

    return emails


def motion_release_email_generator(to, round):
    emails = []

    def _create_motion_list():
        motion_list = "<ul>"
        for motion in round.motion_set.all():
            motion_list += _("<li>%(text)s (%(ref)s)</li>") % {'text': motion.text, 'ref': motion.reference}

            if motion.info_slide:
                motion_list += "   %s\n" % (motion.info_slide)

        motion_list += "</ul>"

        return mark_safe(motion_list)

    context = {
        'TOURN': str(round.tournament),
        'ROUND': round.name,
        'MOTIONS': _create_motion_list(),
    }

    people = Person.objects.filter(id__in=to)
    for person in people:
        context_user = context.copy()
        context_user['USER'] = person.name

        emails.append((context_user, person))

    return emails


def team_speaker_email_generator(to, tournament):
    emails = []

    for team in tournament.team_set.all().prefetch_related('speaker_set', 'break_categories').select_related('institution'):
        context = {
            'TOURN': str(tournament),
            'SHORT': team.short_name,
            'LONG': team.long_name,
            'CODE': team.code_name,
            'BREAK': _(", ").join([breakq.name for breakq in team.break_categories.all()]),
            'SPEAKERS': _(", ").join([p.name for p in team.speaker_set.all()]),
            'INSTITUTION': str(team.institution),
            'EMOJI': team.emoji,
        }

        for speaker in team.speakers:
            try:
                to.remove(speaker.id)
            except ValueError:
                continue

            context_user = context.copy()
            context_user['USER'] = speaker.name

            emails.append((context_user, speaker))

    return emails


def team_draw_email_generator(to, round):
    emails = []
    draw = round.debate_set_with_prefetches(speakers=True).all()
    use_codes = use_team_code_names(round.tournament, False)

    for debate in draw:
        matchup = debate.matchup_codes if use_codes else debate.matchup
        context = {
            'ROUND': round.name,
            'VENUE': debate.venue.name,
            'PANEL': _assemble_panel(debate.adjudicators.with_positions()),
            'DRAW': matchup,
        }

        for dt in debate.debateteam_set.all():
            context_team = context.copy()
            context_team['TEAM'] = dt.team.code_name if use_codes else dt.team.short_name
            context_team['SIDE'] = dt.get_side_name(tournament=round.tournament)

            for speaker in dt.team.speakers:
                try:
                    to.remove(speaker.id)
                except ValueError:
                    continue

                context_user = context_team.copy()
                context_user['USER'] = speaker.name

                emails.append((context_user, speaker))

    return emails
