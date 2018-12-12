from django.urls import re_path
from persistent_message.views import PersistentMessageAPI


urlpatterns = [
    re_path(r'api/v1/messages$', PersistentMessageAPI.as_view()),
    re_path(r'api/v1/messages/(?P<message_id>\d+)$',
            PersistentMessageAPI.as_view()),
]
