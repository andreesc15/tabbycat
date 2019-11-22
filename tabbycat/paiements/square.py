import uuid

from square.client import Client

from settings.core import SQUARE_LOCATION, SQUARE_TOKEN


merchant_support_email = 'tresorerie@liduc.org'

client = Client(
    access_token=SQUARE_TOKEN,
    environment='production',
)

def create_payment(payment, return_url):
    checkout_api = client.checkout

    body = {
        'idempotency_key': str(uuid.uuid1()),
        'order': {
            'reference_id': payment.reference,
            'line_items': []
        },
        'merchant_support_email': merchant_support_email,
        'redirect_url': return_url,
        'note': payment.institution.name,
    }

    if payment.tournament is None:
        body['order']['line_items'].append({
            'name': 'Adhésion',
            'quantity': '1',
            'base_price_money': {
                'amount': 2500,
                'currency': 'CAD',
            }
        })

    if payment.numDebatteurs > 0:
        body['order']['line_items'].append({
            'name': 'Inscription de débatteur',
            'quantity': str(payment.numDebatteurs),
            'base_price_money': {
                'amount': 5000,
                'currency': 'CAD',
            }
        })
    if payment.numJuges > 0:
        body['order']['line_items'].append({
            'name': 'Inscription de juge',
            'quantity': str(payment.numJuges),
            'base_price_money': {
                'amount': 2000,
                'currency': 'CAD',
            }
        })

    result = checkout_api.create_checkout(SQUARE_LOCATION, body)
    if result.is_success():
        payment.checkout = result.body['checkout']['id']
        payment.save()

        return result.body
    elif result.is_error():
        raise Exception(result.errors)


def update_payments(payments):
    orders_api = client.orders

    body = {'order_ids': list(payments)}

    result = orders_api.batch_retrieve_orders(SQUARE_LOCATION, body)
    if result.is_success():
        return result.body
    elif result.is_error():
        raise Exception(result.errors)


def list_payments():
    payments_api = client.payments
    result = payments_api.list_payments()
    if result.is_success():
        return result.body
    elif result.is_error():
        raise Exception(result.errors)


def get_payment(payment):
    payments_api = client.payments

    result = payments_api.get_payment(payment)
    if result.is_success():
        return result.body
    elif result.is_error():
        raise Exception(result.errors)
