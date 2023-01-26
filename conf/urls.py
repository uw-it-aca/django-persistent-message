# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import include, re_path

urlpatterns = [
    re_path(r'^', include('persistent_message.urls')),
]
