import uuid
from django.db import models


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

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_name} → {self.recipient_name} : {self.amount} {self.currency} ({self.status})"