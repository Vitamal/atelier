from django.contrib import admin


class BaseMessageAdmin(admin.ModelAdmin):
    raw_id_fields = [
        'sent_by',
        'created_by'
    ]
    list_display = [
        'id',
        'subject',
        'status',
        'esp_ok_status',
        'sent_by',
        'created_datetime',
        'message_types',
        'sms_part_count',
        'sms_content_length',
        'anonymized_datetime',
    ]
    search_fields = [
        'id',
        'subject',
        'sent_by__id',
        'esp_message_id',
    ]
    readonly_fields = [
        'esp_ok_status',
        'esp_message_id',
    ]
    list_filter = [
        'status',
        'requested_send_datetime',
        'anonymized_datetime',
        'esp_ok_status',
    ]
