from django import forms

class PaymentForm(forms.Form):
    sender_name = forms.CharField(max_length=100, label="Sender's Name")
    sender_email = forms.EmailField(label="Sender Email", required=True)
    sender_contact = forms.CharField(max_length=100, label="Sender's Contact")
    
    recipient_name = forms.CharField(max_length=100, label="Recipient's Name")
    recipient_contact = forms.CharField(max_length=100, label="Recipient's Contact")
    
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")
    
    payment_reference = forms.CharField(max_length=255, required=True, label="Payment Reference")
    
