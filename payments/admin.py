from django.contrib import admin
from .models import Transaction

# Register your models here.
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'recipient_name', 'amount', 'status','payment_reference','transaction_id', 'created_at')
    list_filter = ( 'status', 'created_at')
    search_fields = ('sender_name', 'recipient_name', 'payment_reference')
    ordering = ('-created_at',)
    

