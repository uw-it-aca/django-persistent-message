# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from persistent_message.views import manage
from persistent_message.views.api import MessageAPI, TagGroupAPI


urlpatterns = [
    re_path(r'manage$', manage, name='manage_persistent_messages'),
    re_path(r'api/v1/messages$', MessageAPI.as_view(), name='messages_api'),
    re_path(r'api/v1/messages/(?P<message_id>\d+)$', MessageAPI.as_view(),
            name='message_api'),
    re_path(r'api/v1/tag_groups$', TagGroupAPI.as_view(),
            name='tag_groups_api')
]
