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