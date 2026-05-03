import requests
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import PaymentForm
from .models import Transaction
from decimal import Decimal, ROUND_HALF_UP


# FX rates (MVP - controlled manually)
FX_RATES = {
    "EUR": Decimal('14.5'),
    "GBP": Decimal('17.0'),
    "USD": Decimal('13.2'),
}


def calculate_fee(amount_ghs):
    return (amount_ghs *  Decimal('0.03')) + Decimal('5')  # 3% + 5 GHS


def calculate_transaction(amount, currency):
    rate = FX_RATES.get(currency, Decimal('13.2'))

    converted_amount = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    fee = calculate_fee(converted_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    net_amount = (converted_amount - fee).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return rate, converted_amount, fee, net_amount



def initiate_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            currency = form.cleaned_data['currency']

            # ✅ BACKEND CALCULATION (truth layer)
            fx_rate, converted_amount, fee, net_amount = calculate_transaction(
                amount, currency
            )

            # ✅ CREATE TRANSACTION
            transaction = Transaction.objects.create(
                sender_name=form.cleaned_data['sender_name'],
                sender_email=form.cleaned_data['sender_email'],
                sender_contact=form.cleaned_data['sender_contact'],
                recipient_name=form.cleaned_data['recipient_name'],
                recipient_contact=form.cleaned_data['recipient_contact'],
                amount=amount,
                currency=currency,
                fx_rate=fx_rate,
                converted_amount=converted_amount,
                fee=fee,
                net_amount=net_amount,
                payment_reference=form.cleaned_data['payment_reference'],
                status='pending'
            )

            # ✅ PAYSTACK INIT
            url = "https://api.paystack.co/transaction/initialize"

            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }

            data = {
                "email": transaction.sender_email,
                "amount": int((converted_amount * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)),  # ⚠️ Paystack expects smallest currency unit
                "reference": str(transaction.transaction_id),
                "callback_url": "http://127.0.0.1:8000/payment/callback/",
            }

            response = requests.post(url, json=data, headers=headers)
            res = response.json()

            if res.get('status'):
                return redirect(res['data']['authorization_url'])
            else:
                print(res)

        else:
            print(form.errors)

    else:
        form = PaymentForm()

    return render(request, 'payments/initiate_payment.html', {'form': form})

def payment_callback(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')

    transaction = Transaction.objects.filter(transaction_id=reference).first()

    if transaction:
        transaction.status = 'paid'
        transaction.save()

    return render(request, 'payments/payment_success.html', {
        'transaction': transaction
    })