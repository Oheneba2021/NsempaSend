import uuid
from django.db import models

import string
import secrets

def generate_transaction_id():
    prefix = "NSP"
    random_part = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(8)
    )
    return f"{prefix}-{random_part}"




class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('USD', 'US Dollar'),
    ]

    # 👤 Sender
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    sender_contact = models.CharField(max_length=100)

    # 👥 Recipient
    recipient_name = models.CharField(max_length=100)
    recipient_contact = models.CharField(max_length=100)

    # 💱 Currency Info
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='EUR',
    )

    # 💰 Financial Breakdown
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    fx_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )

    converted_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # 🔗 Payment Tracking
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    transaction_id = models.CharField(
        max_length=12,
        unique=True,
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            while True:
                new_id = generate_transaction_id()
                if not Transaction.objects.filter(transaction_id=new_id).exists():
                    self.transaction_id = new_id
                    break

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sender_name} → {self.recipient_name} : {self.amount} {self.currency} ({self.status})"