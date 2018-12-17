from django.urls import re_path
from persistent_message.views import manage
from persistent_message.views.api import MessageAPI


urlpatterns = [
    re_path(r'manage$', manage, name='manage_messages'),
    re_path(r'api/v1/messages$', MessageAPI.as_view(), name='messages_api'),
    re_path(r'api/v1/messages/(?P<message_id>\d+)$', MessageAPI.as_view(),
            name='message_api')
]
