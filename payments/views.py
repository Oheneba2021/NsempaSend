import requests
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import PaymentForm
from .models import Transaction
from decimal import Decimal, ROUND_HALF_UP
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from .utils import get_exchange_rate
from django.http import JsonResponse


def get_exchange_rate(currency):

    try:

        url = (
            f"https://v6.exchangerate-api.com/v6/"
            f"{settings.EXCHANGE_RATE_API_KEY}/latest/{currency}"
        )

        response = requests.get(url)

        data = response.json()

        rate = data['conversion_rates']['GHS']

        return Decimal(str(rate))

    except Exception:

        # fallback rates
        fallback_rates = {
            "EUR": Decimal('14.5'),
            "GBP": Decimal('17.0'),
            "USD": Decimal('13.2'),
        }

        return fallback_rates.get(currency, Decimal('13.2'))

def get_rate(request):

    currency = request.GET.get('currency')

    rate = get_exchange_rate(currency)

    return JsonResponse({
        'rate': float(rate)
    })

def calculate_fee(amount_ghs):

    return (
        (amount_ghs * Decimal('0.03')) + Decimal('5')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_transaction(amount, currency):

    rate = get_exchange_rate(currency)

    converted_amount = (
        amount * rate
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    fee = calculate_fee(converted_amount)

    net_amount = (
        converted_amount - fee
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

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
                "callback_url": f"{request.build_absolute_uri('/payment/callback/')}",
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

import requests
from django.conf import settings
from django.shortcuts import render

def payment_callback(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')

    print("REFERENCE:", reference)

    # 🔍 Find transaction
    transaction = Transaction.objects.filter(transaction_id=reference).first()

    if not transaction:
        return render(request, 'payments/error.html', {
            'message': 'Transaction not found'
        })

    # 🔒 VERIFY with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    response = requests.get(url, headers=headers)
    res = response.json()

    print("PAYSTACK RESPONSE:", res)

    # ✅ Only mark as paid if VERIFIED
    if res.get('status') and res['data']['status'] == 'success':

        if transaction.status != 'paid':  # prevent duplicate updates
            transaction.status = 'paid'
            transaction.save()
            print("STATUS UPDATED TO PAID")
        
            
        subject = "Payment Receipt"

        html_content = render_to_string(
            'payments/email_receipt.html',
            {'transaction': transaction}
        )

        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            settings.EMAIL_HOST_USER,
            [transaction.sender_email],
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()
        
        return render(request, 'payments/payment_success.html', {
            'transaction': transaction
        })

    else:
        transaction.status = 'failed'
        transaction.save()

        return render(request, 'payments/error.html', {
            'message': 'Payment verification failed'
        })