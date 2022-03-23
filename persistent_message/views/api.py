# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from persistent_message.models import Message, TagGroup, Tag
from persistent_message.decorators import message_admin_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from logging import getLogger
import dateutil.parser
import json

logger = getLogger(__name__)


@method_decorator(message_admin_required, name='dispatch')
class MessageAPI(View):
    def get(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            try:
                message = Message.objects.get(pk=message_id)
                return self.json_response({'message': message.to_json()})
            except Message.DoesNotExist:
                return self.error_response(
                    404, 'Message {} not found'.format(message_id))
        except KeyError:
            messages = []
            for message in sorted(Message.objects.all(), key=lambda m: (
                    m.is_active(), m.modified), reverse=True):
                messages.append(message.to_json())
            return self.json_response({'messages': messages})

    def put(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            self.message = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return self.error_response(
                404, 'Message {} not found'.format(message_id))
        except KeyError:
            return self.error_response(400, 'Missing message ID')

        try:
            self._deserialize(request)
            self.message.save()
            if self.tags is not None:
                self.message.tags.clear()
                self.message.tags.add(*self.tags)
        except ValidationError as ex:
            return self.error_response(400, ex)

        logger.info('Message ({}) updated'.format(self.message.pk))
        return self.json_response({'message': self.message.to_json()})

    def post(self, request, *args, **kwargs):
        self.message = Message()

        try:
            self._deserialize(request)
            self.message.save()
            if self.tags is not None:
                self.message.tags.add(*self.tags)
        except ValidationError as ex:
            return self.error_response(400, ex)

        logger.info('Message ({}) created'.format(self.message.pk))
        return self.json_response({'message': self.message.to_json()})

    def delete(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            message = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return self.error_response(
                404, 'Message {} not found'.format(message_id))
        except KeyError:
            return self.error_response(400, 'Missing message ID')

        message.delete()

        logger.info('Message ({}) deleted'.format(message.pk))
        return self.json_response({})

    def error_response(self, status, message='', content={}):
        content['error'] = '{}'.format(message)
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')

    def json_response(self, content='', status=200):
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')

    def _deserialize(self, request):
        self.tags = None
        try:
            json_data = json.loads(request.body)['message']
            if not any(key in json_data for key in [
                    'content', 'level', 'begins', 'expires', 'tags']):
                raise ValidationError()
        except Exception as ex:
            raise ValidationError('Invalid JSON: {}'.format(request.body))

        if 'content' in json_data:
            self.message.content = json_data['content']
        if 'level' in json_data:
            self.message.level = json_data['level']
        if 'begins' in json_data:
            begins = json_data['begins']
            self.message.begins = dateutil.parser.parse(begins) if (
                begins is not None) else None
        if 'expires' in json_data:
            expires = json_data['expires']
            self.message.expires = dateutil.parser.parse(expires) if (
                expires is not None) else None
        if 'tags' in json_data:
            self.tags = []
            for name in json_data['tags']:
                try:
                    self.tags.append(Tag.objects.get(name=name))
                except Tag.DoesNotExist:
                    raise ValidationError('Invalid tag: {}'.format(name))

        self.message.modified_by = request.user.username


@method_decorator(message_admin_required, name='dispatch')
class TagGroupAPI(View):
    def get(self, request, *args, **kwargs):
        groups = []
        for group in TagGroup.objects.all():
            groups.append(group.to_json())

        return HttpResponse(json.dumps({'tag_groups': groups}),
                            content_type='application/json')
