from django import forms

class PaymentForm(forms.Form):
    sender_name = forms.CharField(max_length=100, label="Sender Name")
    sender_email = forms.EmailField(label="Sender Email")  # ✅ required
    sender_contact = forms.CharField(max_length=100, label="Sender Phone")

    recipient_name = forms.CharField(max_length=100, label="Recipient Name")
    recipient_contact = forms.CharField(max_length=100, label="Recipient Phone")

    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")

    currency = forms.ChoiceField(
        choices=[
            ('EUR', 'Euro (€)'),
            ('GBP', 'British Pound (£)'),
            ('USD', 'US Dollar ($)')
        ],
        label="Currency"
    )

    payment_reference = forms.CharField(
        max_length=255,
        required=True,
        label="Payment Reference"
    )