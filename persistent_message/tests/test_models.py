from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from persistent_message.models import Message, Tag, TagGroup
from unittest import mock


def mocked_current_datetime():
    dt = datetime(2018, 1, 1, 10, 10, 10)
    return timezone.make_aware(dt)


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
    def test_message_expire(self, mock_obj):
        self.message.begins = mocked_current_datetime() + timedelta(days=1)
        self.message.expires = mocked_current_datetime() + timedelta(days=7)
        self.message.save()

        self.assertEqual(self.message.begins.isoformat(),
                         '2018-01-02T10:10:10+00:00')
        self.assertEqual(self.message.expires.isoformat(),
                         '2018-01-08T10:10:10+00:00')

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
            self.tag.to_json(), {'group': 'city', 'name': 'seattle'})

    def test_str(self):
        self.assertEqual(str(self.tag), 'seattle')


class TagGroupTest(TestCase):
    def setUp(self):
        self.group = TagGroup(name='city')
        self.group.save()

    def test_str(self):
        self.assertEqual(str(self.group), 'city')

    def test_json(self):
        tag1 = Tag(name='seattle', group=self.group)
        tag1.save()

        tag2 = Tag(name='tacoma', group=self.group)
        tag2.save()

        self.assertEqual(
            self.group.to_json(),
            {'name': 'city', 'tags': ['seattle', 'tacoma']})

class MessageManagerTest(TestCase):
    def test_get_current_messages(self):
        pass
