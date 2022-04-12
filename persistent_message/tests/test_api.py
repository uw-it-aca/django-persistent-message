# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse
from datetime import timedelta
from persistent_message.models import Message, Tag, TagGroup
from persistent_message.tests import mocked_current_datetime
from persistent_message.views.api import MessageAPI, TagGroupAPI
from unittest import mock
import json


class TagGroupAPITest(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.get(username='manager')

    def test_get(self):
        request = self.factory.get(reverse('tag_groups_api'))
        request.user = self.user
        response = TagGroupAPI.as_view()(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['tag_groups']), 2)


class MessageAPITest(TestCase):
    fixtures = ['test.json']

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def setUp(self, mock_dt):
        self.factory = RequestFactory()
        self.user = User.objects.get(username='manager')

        tag1 = Tag.objects.get(name='Seattle')
        tag2 = Tag.objects.get(name='Tacoma')

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
        self.assertEqual(len(data['messages']), 5)

    def test_get_one(self):
        url = reverse('message_api', kwargs={'message_id': '1'})
        request = self.factory.get(url)
        request.user = self.user
        response = MessageAPI.as_view()(request, message_id=1)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('message').get('id'), 1)
        self.assertEqual(data.get('message').get('content'), 'This is a test.')

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_put(self, mock_dt):
        message = Message.objects.get(content='4')
        json_data = message.to_json()

        self.assertEqual(json_data['content'], '4')
        self.assertEqual(json_data['level'], Message.WARNING_LEVEL)
        self.assertEqual(json_data['tags'], [
            {'group': 'Cities', 'id': 3, 'name': 'Seattle'},
            {'group': 'Cities', 'id': 4, 'name': 'Tacoma'}])

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
            'content': 'Hello World!', 'tags': ['Seattle']}}
        response = self._post(json_data)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data.get('message').get('content'), 'Hello World!')
        self.assertEqual(data.get('message').get('level'), Message.INFO_LEVEL)
        self.assertEqual(data.get('message').get('begins'),
                         '2018-01-01T10:10:10+00:00')
        self.assertEqual(data.get('message').get('expires'), None)
        self.assertEqual(data.get('message').get('tags'),
                         [{'group': 'Cities', 'id': 3, 'name': 'Seattle'}])

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
        self.assertIn(b'Invalid JSON', response.content)

        json_data = {'message': {'content': '', 'tags': ['Bothell']}}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid tag: Bothell", response.content)

        json_data = {'message': {
            'content': '',
            'expires': mocked_current_datetime() - timedelta(days=7),
        }}
        response = self._post(json_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid expires: expires precedes begins",
                      response.content)
