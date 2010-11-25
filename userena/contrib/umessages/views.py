from django.contrib.auth.decorators import login_required
from django.views.generic import list_detail
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.models import User
from django.template import loader
from django.contrib import messages
from django.utils.translation import ugettext as _

from userena.contrib.umessages.models import Message
from userena.contrib.umessages.forms import ComposeForm
from userena import settings as userena_settings

import datetime

@login_required
def message_list(request, page=1, paginate_by=50, mailbox="inbox",
                 fallback_template_name="umessages/message_list.html",
                 extra_context=None, **kwargs):
    """

    List a folder of specific type for this user.

    :param page:
        Integer of the active page used for pagination. Defaults to the first
        page.

    :param paginate_by:
        Integer defining the amount of displayed messages per page.
        Defaults to 50 messages per per page.

    :param mailbox:
        String defining the mailbox that is currently opened. Can be one of the
        following four strings:

        ``inbox``
            Incoming messages.

        ``outbox``
            Sent messsages.

        ``drafts``
            Composed but not sent messages.

        ``trash``
            Messages that are marked as deleted.

    :param fallback_template_name:
        String defining the name of the template that is used to render the
        list of messages when no custom mailbox template is found. Defaults to
        ``umessages/message_list.html``. A custom mailbox template can be
        created with the name of the mailbox append to
        ``message_list_<mailbox>.html``. This template has preference above the
        ``fallback_template_name``.

    :param extra_context:
        A dictionary of variables that are passed on to the template.

    **Context**

    ``message_list``
        A list of messages.

    ``is_paginated``
        A boolean representing whether the results are paginated.

    ``mailbox``
        The current active mailbox.

    If the result is paginated, the context will also contain the following
    variables.

    ``paginator``
        An instance of ``django.core.paginator.Paginator``.

    ``page_obj``
        An instance of ``django.core.paginator.Page``.

    """
    try:
        page = int(request.GET.get("page", None))
    except TypeError, ValueError:
        page = page

    queryset = Message.objects.get_mailbox_for(user=request.user,
                                               mailbox=mailbox)

    # Get the right template
    template_loader = loader.select_template(["umessages/message_list_%(mailbox)s.html" % {"mailbox": mailbox},
                                               fallback_template_name])

    if not extra_context: extra_context = dict()
    extra_context["mailbox"] = mailbox
    return list_detail.object_list(request,
                                   queryset=queryset,
                                   paginate_by=paginate_by,
                                   page=page,
                                   template_name=template_loader.name,
                                   extra_context=extra_context,
                                   template_object_name="message",
                                   **kwargs)

@login_required
def message_detail(request, message_id, template_name="umessages/message_detail.html",
                   use_threaded=True, extra_context=None):
    """
    Detailed view of a message.

    :param message_id:
        Integer suppyling the pk of the message.

    :param template_name:
        String of the template that is rendered to display this view.

    :param use_threaded:
        Boolean that defines if the view get's the parent messages also.

    :param: extra_context:
        Dictionary of variables that will be made available to the template.

    """
    message = Message.objects.get(pk=message_id)
    now = datetime.datetime.now()

    if (message.sender != request.user) and \
       (request.user not in message.recipients.all()):
        raise Http404

    mr = message.messagerecipient_set.get(message=message,
                                          user=request.user)
    if mr.read_at is None:
        mr.read_at = now
        mr.save()

    if not extra_context:
        extra_context = dict()

    extra_context["message"] = message
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)

@login_required
def message_compose(request, recipients=None, parent_id=None,
                    compose_form=ComposeForm,
                    success_url="userena_umessages_inbox",
                    template_name="umessages/compose_form.html",
                    recipient_filter=None, extra_context=None):
    """
    Compose a new message

    :recipients:
        String containing the usernames to whom the message is send to. Can be
        multiple username by seperating them with a ``+`` sign.

    :param parent_msg:
        Integer supplying the pk of the message that is replied to. Defaults to
        ``None``.

    :param compose_form:
        The form that is used for getting neccesary information. Defaults to
        :class:`ComposeForm`.

    :param success_url:
        String containing the named url which to redirect to after successfull
        sending a message. Defaults to ``userena_umessages_inbox``.

    :param template_name:
        String containing the name of the template that is used.

    :param recipient_filter:
        A list of :class:`User` that don"t want to receive any messages.

    :param extra_context:
        Dictionary with extra variables supplied to the template.

    **Context**

    ``form``
        The form that is used.

    """
    initial_data = dict()

    if recipients:
        username_list = [r.strip() for r in recipients.split("+")]
        recipients = [u for u in User.objects.filter(username__in=username_list)]
        initial_data["to"] = recipients

    if parent_id:
        parent_msg = get_object_or_404(Message,
                                       pk=parent_id,
                                       recipients=request.user)
        initial_data["subject"] = "Re: %(subject)s" % {"subject": parent_msg.subject}
        initial_data["to"] = parent_msg.sender
    else: parent_msg = None

    form = compose_form(initial=initial_data)
    if request.method == "POST":
        form = compose_form(request.POST)
        if form.is_valid():
            draft = request.POST.has_key("_draft")
            requested_redirect = request.REQUEST.get("next", False)

            message = form.save(request.user, parent_msg, draft)

            if userena_settings.USERENA_USE_MESSAGES:
                messages.success(request, _('Message is sent.'),
                                 fail_silently=True)

            if requested_redirect:
                return redirect(requested_redirect)
            else:
                return redirect(reverse(success_url))

    if not extra_context:
        extra_context = dict()
    extra_context["form"] = form
    extra_context["recipients"] = recipients
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)

@login_required
@require_http_methods(["POST"])
def message_remove(request, undo=False):
    """
    A ``POST`` to remove messages.

    :param undo:
        A Boolean that if ``True`` unremoves messages.

    POST can have the following keys:

        ``message_pks``
            List of message id's that should be deleted.

        ``next``
            String containing the URI which to redirect to after the keys are
            removed. Redirect defaults to the inbox view.

    The ``next`` value can also be supplied in the URI with ``?next=<value>``.

    """
    message_pks = request.POST.getlist('message_pks')
    redirect_to = request.REQUEST.get('next', False)

    if message_pks:
        # Check that all values are integers.
        valid_message_pk_list = set()
        for pk in message_pks:
            try: valid_pk = int(pk)
            except (TypeError, ValueError): pass
            else:
                valid_message_pk_list.add(valid_pk)

        # Delete all the messages, if they belong to the user.
        now = datetime.datetime.now()
        changed_message_list = set()
        for pk in valid_message_pk_list:
            message = get_object_or_404(Message,
                                        pk=pk)

            # Check if the user is the owner
            if message.sender == request.user:
                if undo:
                    message.sender_deleted_at = None
                else:
                    message.sender_deleted_at = now
                message.save()
                changed_message_list.add(message.pk)

            # Check if the user is a recipient of the message
            if request.user in message.recipients.all():
                mr = message.messagerecipient_set.get(user=request.user,
                                                      message=message)
                if undo:
                    mr.deleted_at = None
                else:
                    mr.deleted_at = now
                mr.save()
                changed_message_list.add(message.pk)

        if (len(changed_message_list) > 0) and userena_settings.USERENA_USE_MESSAGES:
            if len(changed_message_list) > 1:
                if undo:
                    messages.success(request, _('Messages are successfully restored.'), fail_silently=True)
                else:
                    messages.success(request, _('Messages are successfully removed.'), fail_silently=True)
            else:
                if undo:
                    messages.success(request, _('Message is successfully restored.'), fail_silently=True)
                else:
                    messages.success(request, _('Message is successfully removed.'), fail_silently=True)

    if redirect_to: return redirect(redirect_to)
    else: return redirect(reverse('userena_umessages_inbox'))

@login_required
@require_http_methods(["POST"])
def message_unremove(request):
    return redirect(reverse('userena_umessages_inbox'))
