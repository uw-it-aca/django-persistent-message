from django.db import models
from django.contrib import messages
from django.utils import timezone
import bleach

MESSAGE_ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + [
    'span', 'h1', 'h2', 'h3', 'h4']
MESSAGE_ALLOWED_ATTRIBUTES = bleach.sanitizer.ALLOWED_ATTRIBUTES.copy()
MESSAGE_ALLOWED_ATTRIBUTES['*'] = ['class', 'style', 'aria-hidden']
MESSAGE_ALLOWED_STYLES = ['font-size', 'color']


class MessageManager(models.Manager):
    def get_current_messages(self):
        now = timezone.now()
        return super(MessageManager, self).get_queryset().filter(
            Q(expires__gt=now) | Q(expires__isnull=True),
            begins__lte=now).order_by('start')


class MessageTag(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Message(models.Model):
    DEBUG_LEVEL = messages.DEBUG
    INFO_LEVEL = messages.INFO
    SUCCESS_LEVEL = messages.SUCCESS
    WARNING_LEVEL = messages.WARNING
    DANGER_LEVEL = messages.ERROR

    LEVEL_CHOICES = (
        (DEBUG_LEVEL, 'Debug'),
        (INFO_LEVEL, 'Information'),
        (SUCCESS_LEVEL, 'Success'),
        (WARNING_LEVEL, 'Warning'),
        (DANGER_LEVEL, 'Danger'),
    )

    content = models.TextField()
    level = models.IntegerField(choices=LEVEL_CHOICES, default=INFO_LEVEL)
    begins = models.DateTimeField()
    expires = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=50)
    tags = models.ManyToManyField(MessageTag)

    objects = MessageManager()

    def save(self, *args, **kwargs):
        self.content = self.sanitize_content(self.content)

        if (self.begins is None):
            self.begins = self.current_datetime()

        super(Message, self).save(*args, **kwargs)

    def to_json(self):
        return {
            'content': self.content,
            'level': self.level,
            'begins': self.begins.isoformat() if (
                self.begins is not None) else None,
            'expires': self.expires.isoformat() if (
                self.expires is not None) else None,
            'created': self.created.isoformat() if (
                self.created is not None) else None,
            'modified': self.modified.isoformat() if (
                self.modified is not None) else None,
            'modified_by': self.modified_by,
            'tags': [m.name for m in self.tags.all()],
        }

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
