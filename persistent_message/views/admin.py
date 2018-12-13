from persistent_message.models import Message, TagGroup
from persistent_message.decorators import message_admin_required
from django.shortcuts import render


@message_admin_required
def manage(request):
    context = {}
    return render(request, 'manage.html', context)
