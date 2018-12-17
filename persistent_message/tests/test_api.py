from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse
from datetime import timedelta
from persistent_message.models import Message, Tag, TagGroup
from persistent_message.tests import mocked_current_datetime
from persistent_message.views.api import MessageAPI
from unittest import mock
import json


class MessageAPITest(TestCase):
    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def setUp(self, mock_dt):
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
        message2.begins = mocked_current_datetime() + timedelta(days=7)
        message2.save()
        message2.tags.add(tag2)

        message3 = Message(content='3')
        message3.save()

        message4 = Message(content='4', level=Message.WARNING_LEVEL)
        message4.save()
        message4.tags.add(tag1, tag2)

    def test_get_all(self):
        request = self.factory.get(reverse('messages_api'))
        request.user = self.user
        response = MessageAPI.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['messages']), 4)

    def test_get_one(self):
        url = reverse('message_api', kwargs={'message_id': '1'})
        request = self.factory.get(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=1)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('message').get('id'), 1)
        self.assertEqual(data.get('message').get('content'), '1')

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_put(self, mock_dt):
        message = Message.objects.get(pk=4)
        json_data = message.to_json()

        self.assertEqual(json_data['content'], '4')
        self.assertEqual(json_data['level'], Message.WARNING_LEVEL)
        self.assertEqual(json_data['tags'], ['seattle', 'tacoma'])

        json_data['content'] = 'abc'
        json_data['level'] = Message.DANGER_LEVEL
        json_data['expires'] = mocked_current_datetime() + timedelta(days=7)
        json_data['tags'] = []  # Remove all tags

        url = reverse('message_api', kwargs={'message_id': message.pk})
        request = self.factory.put(
            url, data={'message': json_data}, content_type='application/json')
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=message.pk)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('message').get('content'), 'abc')
        self.assertEqual(data.get('message').get('level'),
                         Message.DANGER_LEVEL)
        self.assertEqual(data.get('message').get('expires'),
                         '2018-01-08T10:10:10+00:00')
        self.assertEqual(json_data['tags'], [])

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_post(self, mock_dt):
        json_data = {'message': {
            'content': 'Hello World!', 'tags': ['seattle']}}
        response = self._post(json_data)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('message').get('content'), 'Hello World!')
        self.assertEqual(data.get('message').get('level'), Message.INFO_LEVEL)
        self.assertEqual(data.get('message').get('begins'),
                         '2018-01-01T10:10:10+00:00')
        self.assertEqual(data.get('message').get('expires'), None)
        self.assertEqual(data.get('message').get('tags'), ['seattle'])

    def test_delete(self):
        url = reverse('message_api', kwargs={'message_id': '4'})
        request = self.factory.delete(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=4)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {})

    def _post(self, json_data):
        request = self.factory.post(
            reverse('messages_api'), data=json_data,
            content_type='application/json')
        request.user = self.user
        response = MessageAPI.as_view()(request)
        return response


class MessageAPIErrors(MessageAPITest):
    def test_no_access(self):
        request = self.factory.get(reverse('messages_api'))
        request.user = User.objects.create_user(username='nobody', password='')
        response = MessageAPI.as_view()(request)
        self.assertEqual(response.status_code, 401)

    def test_missing_id(self):
        url = reverse('message_api', kwargs={'message_id': '1'})

        # PUT
        request = self.factory.put(url)
        request.user = self.user
        response = MessageAPI.as_view()(request)
        self.assertEqual(response.status_code, 400)

        # DELETE
        request = self.factory.delete(url)
        request.user = self.user
        response = MessageAPI.as_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_message_not_found(self):
        url = reverse('message_api', kwargs={'message_id': '100'})

        # GET
        request = self.factory.get(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=100)
        self.assertEqual(response.status_code, 404)

        # PUT
        request = self.factory.put(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=100)
        self.assertEqual(response.status_code, 404)

        # DELETE
        request = self.factory.delete(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=100)
        self.assertEqual(response.status_code, 404)

    def test_post_data_errors(self):
        json_data = ''
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid JSON', response.content)

        json_data = {}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid JSON', response.content)

        json_data = {'message': {}}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing: 'content'", response.content)

        json_data = {'message': {'content': '', 'tags': ['olympia']}}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid tag: olympia", response.content)

        json_data = {'message': {
            'content': '',
            'expires': mocked_current_datetime() - timedelta(days=7),
        }}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid expires: expires precedes begins",
                      response.content)
