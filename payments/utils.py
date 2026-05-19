import requests
from django.conf import settings


def get_exchange_rate(currency):

    url = (
        f"https://v6.exchangerate-api.com/v6/"
        f"{settings.EXCHANGE_RATE_API_KEY}/latest/{currency}"
    )

    response = requests.get(url)

    data = response.json()

    return data['conversion_rates']['GHS']