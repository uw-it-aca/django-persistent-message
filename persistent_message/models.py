# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.db import models
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.template import Template, Context
from django.utils import timezone
import bleach

MESSAGE_ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + [
    'br', 'p', 'span', 'h1', 'h2', 'h3', 'h4']
MESSAGE_ALLOWED_ATTRIBUTES = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
MESSAGE_ALLOWED_ATTRIBUTES['*'] = ['class', 'style', 'aria-hidden']
MESSAGE_ALLOWED_STYLES = ['font-size', 'color']


class TagGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def to_json(self):
        return {
            'id': self.pk,
            'name': self.name,
            'tags': [t.to_json() for t in self.tag_set.all()],
        }

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.SlugField(unique=True)
    group = models.ForeignKey(TagGroup, on_delete=models.CASCADE)

    def to_json(self):
        return {
            'id': self.pk,
            'name': self.name,
            'group': str(self.group),
        }

    def __str__(self):
        return self.name


class MessageManager(models.Manager):
    def active_messages(self, level=None, tags=[]):
        now = Message.current_datetime()

        kwargs = {'begins__lte': now}
        if level is not None:
            kwargs['level'] = level

        if len(tags):
            kwargs['tags__name__in'] = tags

        return super(MessageManager, self).get_queryset().filter(
            Q(expires__gt=now) | Q(expires__isnull=True), **kwargs).order_by(
                '-level', '-begins').distinct()


class Message(models.Model):
    INFO_LEVEL = messages.INFO
    SUCCESS_LEVEL = messages.SUCCESS
    WARNING_LEVEL = messages.WARNING
    DANGER_LEVEL = messages.ERROR

    LEVEL_CHOICES = (
        (INFO_LEVEL, 'Info'),
        (SUCCESS_LEVEL, 'Success'),
        (WARNING_LEVEL, 'Warning'),
        (DANGER_LEVEL, 'Danger'),
    )

    content = models.TextField(blank=True)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=INFO_LEVEL)
    begins = models.DateTimeField()
    expires = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=50)
    tags = models.ManyToManyField(Tag)

    objects = MessageManager()

    def is_active(self, now=None):
        if not now:
            now = self.current_datetime()
        return (self.begins is not None and self.begins <= now and (
            self.expires is None or now < self.expires))

    def clean(self):
        self.content = self.sanitize_content(self.content)

        if (self.begins is None or self.begins == ''):
            self.begins = self.current_datetime()

        if (self.expires is not None and self.expires <= self.begins):
            raise ValidationError('Invalid expires: expires precedes begins')

    def save(self, *args, **kwargs):
        self.full_clean(exclude=['begins', 'modified_by'])
        super(Message, self).save(*args, **kwargs)

    def to_json(self, now=None):
        return {
            'id': self.pk,
            'content': self.content,
            'level': self.level,
            'level_name': self.get_level_display(),
            'begins': self.begins.isoformat() if (
                self.begins is not None) else None,
            'expires': self.expires.isoformat() if (
                self.expires is not None) else None,
            'created': self.created.isoformat() if (
                self.created is not None) else None,
            'modified': self.modified.isoformat() if (
                self.modified is not None) else None,
            'modified_by': self.modified_by,
            'tags': [tag.to_json() for tag in self.tags.all()],
            'is_active': self.is_active(now),
        }

    def render(self, context={}):
        return Template(self.content).render(Context(context))

    @staticmethod
    def current_datetime():
        return timezone.now()

    @staticmethod
    def sanitize_content(content):
        return bleach.clean(content,
                            tags=MESSAGE_ALLOWED_TAGS,
                            attributes=MESSAGE_ALLOWED_ATTRIBUTES,
                            styles=MESSAGE_ALLOWED_STYLES)

    def __str__(self):
        return self.content
