from persistent_message.models import PersistentMessage
from PersistentMessage.decorators import message_admin_required
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from logging import getLogger
import json

logger = getLogger(__name__)


@method_decorator(message_admin_required, name='dispatch')
class PersistentMessageAPI(View):
    def get(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            try:
                message = PersistentMessage.objects.get(pk=message_id)
                return self.json_response({'message': message.json_data()})
            except PersistentMessage.DoesNotExist:
                return self.error_response(
                    404, 'Message {} not found'.format(message_id))
        except KeyError:
            messages = []
            for message in PersistentMessage.objects.all():
                messages.append(message.json_data())
            return self.json_response({'messages': messages})

    def put(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            message = PersistentMessage.objects.get(pk=message_id)
        except PersistentMessage.DoesNotExist:
            return self.error_response(
                404, 'Message {} not found'.format(message_id))
        except KeyError:
            return self.error_response(400, 'Missing message ID')

        message = PersistentMessage()
        # TODO
        message.store()

        logger.info('')  # TODO

        return self.json_response({'message': message.json_data()})

    def post(self, request, *args, **kwargs):
        message = PersistentMessage()
        # TODO
        message.store()

        logger.info('')  # TODO

        return self.json_response({'message': message.json_data()})

    def delete(self, request, *args, **kwargs):
        try:
            message_id = kwargs['message_id']
            message = PersistentMessage.objects.get(pk=message_id)
        except PersistentMessage.DoesNotExist:
            return self.error_response(
                404, 'Message {} not found'.format(message_id))
        except KeyError:
            return self.error_response(400, 'Missing message ID')

        message.delete()

        logger.info('')  # TODO

        return self.json_response()

    def error_response(self, status, message='', content={}):
        content['error'] = '{}'.format(message)
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')

    def json_response(self, content='', status=200):
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type='application/json')
