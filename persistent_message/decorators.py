# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.module_loading import import_string
from django.shortcuts import render


def is_message_admin(request):
    return request.user.is_superuser


def message_admin_required(view_func):
    """
    View decorator that checks whether the user is permitted to administer
    messages. Calls login_required in case the user is not authenticated.
    """
    def wrapper(request, *args, **kwargs):
        func_str = getattr(
            settings, 'PERSISTENT_MESSAGE_AUTH_MODULE',
            'persistent_message.decorators.is_message_admin')
        auth_func = import_string(func_str)

        if auth_func(request):
            return view_func(request, *args, **kwargs)

        return render(request, 'access_denied.html', status=401)

    return login_required(function=wrapper)
