import uuid

from django.db import models

# Create your models here.
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('failed', 'Failed'), 
        
    ]
    
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField(blank=False, null=False)
    sender_contact = models.CharField(max_length=100)
    
    recipient_name = models.CharField(max_length=100)
    recipient_contact = models.CharField(max_length=100)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2 )
    
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f" {self.sender_name} -> { self.recipient_name} : {self.amount} ({self.status})  "