# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.utils import timezone
from datetime import datetime


def mocked_current_datetime():
    dt = datetime(2018, 1, 1, 10, 10, 10)
    return timezone.make_aware(dt)
