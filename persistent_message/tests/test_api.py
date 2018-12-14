from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse
from persistent_message.models import Message, Tag, TagGroup
from persistent_message.tests import mocked_current_datetime
from persistent_message.views.api import MessageAPI
from unittest import mock
import json


class MessageAPITest(TestCase):
    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def setUp(self, mock_obj):
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='manager', email='manager@...', password='top_secret')

        group = TagGroup(name='city')
        group.save()

        tag1 = Tag(name='seattle', group=group)
        tag1.save()

        tag2 = Tag(name='tacoma', group=group)
        tag2.save()

        message1 = Message(content='1')
        message1.save()
        message1.tags.add(tag1)

        message2 = Message(content='2')
        message2.expires = mocked_current_datetime()
        message2.save()
        message2.tags.add(tag2)

        message3 = Message(content='3')
        message3.save()

        message4 = Message(content='4', level=Message.WARNING_LEVEL)
        message4.save()
        message4.tags.add(tag1, tag2)

    def test_get_no_access(self):
        request = self.factory.get(reverse('messages_api'))
        request.user = User.objects.create_user(username='nobody', password='')
        response = MessageAPI.as_view()(request)
        self.assertEqual(response.status_code, 401)

    def test_get_all(self):
        request = self.factory.get(reverse('messages_api'))
        request.user = self.user
        response = MessageAPI.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['messages']), 4)

    def test_get_one(self):
        kwargs = {'message_id': '1'}
        url = reverse('message_api', kwargs=kwargs)
        request = self.factory.get(url, kwargs=kwargs)
        request.user = self.user
        response = MessageAPI.as_view()(request, **kwargs)

        self.assertEqual(response.status_code, 200)

    def test_put(self):
        pass

    def test_post(self):
        pass

    def test_delete(self):
        pass
