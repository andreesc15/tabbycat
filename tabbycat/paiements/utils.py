from django.db.models import Q

from participants.models import Institution, Person
from tournaments.models import Tournament

from .models import Payment
from .square import list_payments


STATUTS = {
    'OPEN': Payment.STATUT_OUVERT,
    'COMPLETED': Payment.STATUT_TERMINE,
    'CANCELED': Payment.STATUT_ANNULE,
    'FAILED': Payment.STATUT_ECHOUE,
}


def update_or_create_payments():
    orders = list_payments()

    for order in orders['payments']:
        try:
            payment = Payment.objects.get(order=order['id'])
        except Payment.DoesNotExist:
            create_from_order(order)
            continue

        pay_state = STATUTS[order['status']]
        if payment.statut != pay_state:
            payment.statut = pay_state
            payment.save()


def create_from_order(order):
    note = order.get('note', '').split("/")
    # Note format: "Tournament/Inst|Names|..."
    if len(note) != 2:
        return

    personnes = note[1].split("|")
    inst = personnes.pop(0)

    institution = Institution.objects.get(code=inst)
    tournament = Tournament.objects.none()
    if note[0] != 'adhesion':
        tournament = Tournament.objects.get(slug=note[0])

    paiement = Payment(
        order=order['id'], tournament=tournament, institution=institution,
        methode=Payment.METHODE_CARTE, statut=STATUTS[order['status']],
        montant=order['total_money']['amount'],
    )
    paiement.save()

    if len(personnes) > 0:
        personnes = Person.objects.filter(
            Q(adjudicator__tournament=tournament) | Q(speaker__team__tournament=tournament),
            name__in=personnes
        ).distinct()
        if personnes.exists():
            paiement.personnes.add(*personnes)

    return paiement
