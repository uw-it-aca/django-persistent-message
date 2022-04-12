# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from persistent_message.decorators import message_admin_required
from persistent_message.models import Message
from django.urls import reverse
from django.shortcuts import render
from django import template


@message_admin_required
def manage(request):
    context = {
        'session_id': request.session.session_key,
        'message_api': reverse('messages_api'),
        'tags_api': reverse('tag_groups_api'),
        'message_levels': Message.LEVEL_CHOICES,
    }

    try:
        template.loader.get_template('persistent_message/manage_wrapper.html')
        context['wrapper_template'] = 'persistent_message/manage_wrapper.html'
    except template.TemplateDoesNotExist:
        context['wrapper_template'] = 'manage_wrapper.html'

    return render(request, 'manage.html', context)
