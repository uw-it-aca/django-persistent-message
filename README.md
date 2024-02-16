# django-persistent-message

[![Build Status](https://github.com/uw-it-aca/django-persistent-message/workflows/tests/badge.svg?branch=main)](https://github.com/uw-it-aca/django-persistent-message/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/django-persistent-message/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/django-persistent-message?branch=main)
[![PyPi Version](https://img.shields.io/pypi/v/django-persistent-message.svg)](https://pypi.python.org/pypi/django-persistent-message)
![Python versions](https://img.shields.io/badge/python-3.10-blue.svg)


This app adds authoring and publishing of persistent messages to your Django
project.  Messages can be filtered for display by message level and custom tags
provided by your project.

### Include the persistent_message URLs

Add the persistent_message URLs to your `project/urls.py`:

```
path('persistent_messages/', include('persistent_message.urls')),
```

### Message Level

Messages can be set to one of four levels: Info, Success, Warning, Danger.

### Message Tags

Tags provide another way to filter the display of messages to specific
users or conditions.  Tags should be created by way of a fixture file in your
application.  See `persistent_message/fixtures/test.json` for an example.

### Message Rendering

Message.render will render the message as a Django template and return the
rendered string, using a passed context dictionary.

### Message Admin Authorization

By default, Django superusers can add and edit persistent messages in your
project.  To customize this behavior, add `PERSISTENT_MESSAGE_AUTH_MODULE` to
your Django settings file.  This setting should contain a dotted path string
of a module in your application that returns a boolean indicating whether the
current user is allowed to author messages.

```
PERSISTENT_MESSAGE_AUTH_MODULE = "my_app.auth.is_message_admin"
```
