from django.contrib import admin

from flexitkt.flexitkt_messages import basemessage_admin
from flexitkt.flexitkt_messages.models import MessageReceiver, BaseMessage, SystemMessage, BaseMessageAttachment


class MessageReceiverAdmin(admin.ModelAdmin):
    raw_id_fields = [
        'message',
        'user',
    ]
    list_display = [
        'id',
        'send_to',
        'user',
        'status',
        'sent_datetime',
        'message',
        'message_type',
        'get_message_sent_by',
    ]
    search_fields = [
        '=id',
        'send_to',
        '=user__id',
        '=message__id',
    ]
    list_filter = [
        'status',
        'sent_datetime',
        'message_type',
    ]

    def get_message_sent_by(self, obj):
        return obj.message.sent_by
    get_message_sent_by.short_description = 'Message sent by'


admin.site.register(MessageReceiver, MessageReceiverAdmin)
admin.site.register(BaseMessage, basemessage_admin.BaseMessageAdmin)


class SystemMessageAdmin(basemessage_admin.BaseMessageAdmin):
    pass


admin.site.register(SystemMessage, SystemMessageAdmin)


class MessageAttachmentAdmin(admin.ModelAdmin):
    pass


admin.site.register(BaseMessageAttachment, MessageAttachmentAdmin)
