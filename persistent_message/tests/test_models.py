from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from persistent_message.models import Message, Tag, TagGroup
from persistent_message.tests import mocked_current_datetime
from unittest import mock


class MessageTest(TestCase):
    def setUp(self):
        self.message = Message()
        self.message.content = 'Hello World!'

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_attr(self, mock_obj):
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
    def test_message_active(self, mock_obj):
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
    def test_json(self, mock_obj):
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
        group = TagGroup(name='city')
        group.save()

        tag1 = Tag(name='seattle', group=group)
        tag1.save()

        tag2 = Tag(name='tacoma', group=group)
        tag2.save()

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


class TagTest(TestCase):
    def setUp(self):
        group = TagGroup(name='city')
        group.save()

        self.tag = Tag(name='seattle', group=group)
        self.tag.save()

    def test_json(self):
        self.assertEqual(
            self.tag.to_json(),
            {'id': 1, 'group': 'city', 'name': 'seattle'})

    def test_str(self):
        self.assertEqual(str(self.tag), 'seattle')


class TagGroupTest(TestCase):
    def setUp(self):
        self.group = TagGroup(name='city')
        self.group.save()

        tag1 = Tag(name='seattle', group=self.group)
        tag1.save()

        tag2 = Tag(name='tacoma', group=self.group)
        tag2.save()

    def test_str(self):
        self.assertEqual(str(self.group), 'city')

    def test_json(self):
        self.assertEqual(
            self.group.to_json(),
            {'id': 1, 'name': 'city', 'tags': ['seattle', 'tacoma']})


class MessageManagerTest(TestCase):
    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def setUp(self, mock_obj):
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

    def test_all_messages(self):
        results = Message.objects.all()
        self.assertEqual([str(m) for m in results], ['1', '2', '3', '4'])

    @mock.patch('persistent_message.models.Message.current_datetime',
                side_effect=mocked_current_datetime)
    def test_active_messages(self, mock_obj):
        results = Message.objects.active_messages()
        self.assertEqual([str(m) for m in results], ['4', '1', '3'])

        results = Message.objects.active_messages(
            tags=['seattle', 'tacoma'])
        self.assertEqual([str(m) for m in results], ['4', '1'])

        results = Message.objects.active_messages(level=Message.WARNING_LEVEL)
        self.assertEqual([str(m) for m in results], ['4'])
