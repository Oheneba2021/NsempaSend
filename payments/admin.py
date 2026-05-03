from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'sender_name',
        'recipient_name',
        'amount',
        'currency',
        'fx_rate',
        'converted_amount',
        'fee',
        'net_amount',
        'status',
        'created_at',
    )

    list_filter = (
        'currency',
        'status',
        'created_at',
    )

    search_fields = (
        'sender_name',
        'recipient_name',
        'sender_email',
        'payment_reference',
        'transaction_id',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'transaction_id',
        'created_at',
        'fx_rate',
        'converted_amount',
        'fee',
        'net_amount',
    )

    fieldsets = (
        ("Sender Information", {
            'fields': ('sender_name', 'sender_email', 'sender_contact')
        }),

        ("Recipient Information", {
            'fields': ('recipient_name', 'recipient_contact')
        }),

        ("Transaction Details", {
            'fields': ('amount', 'currency', 'fx_rate')
        }),

        ("Financial Breakdown", {
            'fields': ('converted_amount', 'fee', 'net_amount')
        }),

        ("System Fields", {
            'fields': ('payment_reference', 'transaction_id', 'status', 'created_at')
        }),
    )