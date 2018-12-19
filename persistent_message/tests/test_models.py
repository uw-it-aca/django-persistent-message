from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from persistent_message.models import Message, Tag, TagGroup
from persistent_message.tests import mocked_current_datetime
from unittest import mock


class PersistentMessageTestCase(TestCase):
    fixtures = ['test.json']


class MessageTest(PersistentMessageTestCase):
    def setUp(self):
        self.message = Message()
        self.message.content = 'Hello World!'

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_attr(self, mock_dt):
        # Unsaved model
        self.assertEqual(self.message.pk, None)
        self.assertEqual(self.message.content, 'Hello World!')
        self.assertEqual(self.message.level, self.message.INFO_LEVEL)
        self.assertEqual(self.message.begins, None)
        self.assertEqual(self.message.expires, None)
        self.assertEqual(self.message.created, None)
        self.assertEqual(self.message.modified, None)
        self.assertEqual(self.message.modified_by, '')

        # Save it
        self.message.modified_by = 'javerage'
        self.message.save()
        self.assertEqual(self.message.pk, 1)
        self.assertEqual(self.message.content, 'Hello World!')
        self.assertEqual(self.message.level, self.message.INFO_LEVEL)
        self.assertEqual(self.message.begins.isoformat(),
                         '2018-01-01T10:10:10+00:00')
        self.assertEqual(self.message.expires, None)
        self.assertEqual(self.message.modified_by, 'javerage')
        # These are 'auto_now' dates
        self.assertLess(self.message.created, timezone.now())
        self.assertLess(self.message.modified, timezone.now())

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_message_active(self, mock_dt):
        # Expires not defined
        self.message.save()
        self.assertEqual(self.message.begins.isoformat(),
                         '2018-01-01T10:10:10+00:00')
        self.assertEqual(self.message.expires, None)
        self.assertEqual(self.message.is_active(), True)

        # Begins is past, expires is future
        self.message.expires = mocked_current_datetime() + timedelta(days=7)
        self.message.save()
        self.assertEqual(self.message.begins.isoformat(),
                         '2018-01-01T10:10:10+00:00')
        self.assertEqual(self.message.expires.isoformat(),
                         '2018-01-08T10:10:10+00:00')
        self.assertEqual(self.message.is_active(), True)

        # Begins and expires are past
        self.message.begins = mocked_current_datetime() - timedelta(days=15)
        self.message.expires = mocked_current_datetime() - timedelta(days=7)
        self.message.save()
        self.assertEqual(self.message.begins.isoformat(),
                         '2017-12-17T10:10:10+00:00')
        self.assertEqual(self.message.expires.isoformat(),
                         '2017-12-25T10:10:10+00:00')
        self.assertEqual(self.message.is_active(), False)

        # Begins and expires are future
        self.message.begins = mocked_current_datetime() + timedelta(days=1)
        self.message.expires = mocked_current_datetime() + timedelta(days=7)
        self.message.save()
        self.assertEqual(self.message.begins.isoformat(),
                         '2018-01-02T10:10:10+00:00')
        self.assertEqual(self.message.expires.isoformat(),
                         '2018-01-08T10:10:10+00:00')
        self.assertEqual(self.message.is_active(), False)

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_json(self, mock_dt):
        self.message.modified_by = 'javerage'
        self.message.save()

        json_data = self.message.to_json()
        self.assertEqual(json_data['content'], 'Hello World!')
        self.assertEqual(json_data['level'], self.message.INFO_LEVEL)
        self.assertEqual(json_data['begins'], '2018-01-01T10:10:10+00:00')
        self.assertEqual(json_data['expires'], None)
        self.assertEqual(json_data['modified_by'], 'javerage')
        self.assertEqual(json_data['tags'], [])

    def test_tags(self):
        tag1 = Tag.objects.get(name='seattle')
        tag2 = Tag.objects.get(name='tacoma')

        self.message.save()
        self.message.tags.add(tag1, tag2)

        json_data = self.message.to_json()
        self.assertEqual(json_data['tags'], ['seattle', 'tacoma'])

    def test_str(self):
        self.assertEqual(str(self.message), 'Hello World!')

    def test_sanitize_content(self):
        self.assertRaises(TypeError, self.message.sanitize_content, None)
        self.assertRaises(TypeError, self.message.sanitize_content, 1.75)

        self.assertEqual(
            self.message.sanitize_content('Hello World!'),
            'Hello World!')

        self.assertEqual(
            self.message.sanitize_content(
                '<span style="font-size: 12px; background-image: x; '
                'color: red;">OK</span>'),
            '<span style="font-size: 12px; color: red;">OK</span>')

        self.assertEqual(
            self.message.sanitize_content('<i aria-hidden="true"></i>'),
            '<i aria-hidden="true"></i>')

        self.assertEqual(
            self.message.sanitize_content('<a href="http://uw.edu">UW</a>'),
            '<a href="http://uw.edu">UW</a>')

        self.assertEqual(
            self.message.sanitize_content('<h2>h2</h2>'),
            '<h2>h2</h2>')

        self.assertEqual(
            self.message.sanitize_content('<b><i>x'),
            '<b><i>x</i></b>')

        self.assertEqual(
            self.message.sanitize_content('<script>alert("x");</script>'),
            '&lt;script&gt;alert("x");&lt;/script&gt;')


class TagTest(PersistentMessageTestCase):
    def test_json(self):
        tag = Tag.objects.get(name='seattle')
        self.assertEqual(
            tag.to_json(),
            {'id': 3, 'group': 'Cities', 'name': 'seattle'})

    def test_str(self):
        tag = Tag.objects.get(name='seattle')
        self.assertEqual(str(tag), 'seattle')


class TagGroupTest(PersistentMessageTestCase):
    def test_str(self):
        group = TagGroup.objects.get(name='Cities')
        self.assertEqual(str(group), 'Cities')

    def test_json(self):
        group = TagGroup.objects.get(name='States')
        self.assertEqual(
            group.to_json(),
            {'id': 1, 'name': 'States', 'tags': [
                {'group': 'States', 'id': 1, 'name': 'washington'},
                {'group': 'States', 'id': 2, 'name': 'oregon'}]})


class MessageManagerTest(PersistentMessageTestCase):
    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def setUp(self, mock_dt):
        tag1 = Tag.objects.get(name='seattle')
        tag2 = Tag.objects.get(name='tacoma')

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

    def test_all_messages(self):
        results = Message.objects.all()
        self.assertEqual([str(m) for m in results], ['1', '2', '3', '4'])

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_active_messages(self, mock_dt):
        results = Message.objects.active_messages()
        self.assertEqual([str(m) for m in results], ['4', '1', '3'])

        results = Message.objects.active_messages(
            tags=['seattle', 'tacoma'])
        self.assertEqual([str(m) for m in results], ['4', '1'])

        results = Message.objects.active_messages(level=Message.WARNING_LEVEL)
        self.assertEqual([str(m) for m in results], ['4'])
