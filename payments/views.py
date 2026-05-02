import requests
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import PaymentForm
from .models import Transaction

def initiate_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():

            transaction = Transaction.objects.create(
                sender_name=form.cleaned_data['sender_name'],
                sender_email=form.cleaned_data['sender_email'],
                sender_contact=form.cleaned_data['sender_contact'],
                recipient_name=form.cleaned_data['recipient_name'],
                recipient_contact=form.cleaned_data['recipient_contact'],
                amount=form.cleaned_data['amount'],
                payment_reference=form.cleaned_data.get('payment_reference'),
                status='pending'
            )

            # ✅ Use transaction_id as Paystack reference
            reference = str(transaction.transaction_id)

            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }

            data = {
                "email": transaction.sender_email,  # ⚠️ must be valid email
                "amount": int(transaction.amount * 100),  # convert to pesewas
                "reference": reference,
                "callback_url": "http://127.0.0.1:8000/payment/callback/",
            }

            response = requests.post(url, json=data, headers=headers)
            res = response.json()

            if res['status']:
                return redirect(res['data']['authorization_url'])
            else:
                print(res)  # debug
                return render(request, 'payments/error.html', {
                    'message': res.get('message', 'Payment initialization failed')
                })

        else:
            print(form.errors)

    else:
        form = PaymentForm()

    return render(request, 'payments/initiate_payment.html', {'form': form})


from django.shortcuts import render
from .models import Transaction

def payment_callback(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')

    transaction = Transaction.objects.filter(transaction_id=reference).first()

    return render(request, 'payments/payment_success.html', {
        'transaction': transaction
    })