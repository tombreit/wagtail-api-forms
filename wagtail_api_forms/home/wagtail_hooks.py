from django.urls import reverse

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.menu import MenuItem
from wagtail.snippets.wagtail_hooks import SnippetsMenuItem

from .models import FooterLinks


@hooks.register('construct_main_menu')
def hide_orig_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'snippets']


@hooks.register('register_settings_menu_item')
def register_snippet_as_settings_menu_item():
    return SnippetsMenuItem(
        _('Snippets'),
        reverse('wagtailsnippets:index'),
        icon_name='snippet',
        order=500
    )


@hooks.register('before_create_snippet')
def block_snippet_creation(request, instance):
    if hasattr(instance, "footer_links") and FooterLinks.objects.exists():
        messages.error(request, _('There can only be one Footer Links object.'))
        return redirect('wagtailsnippets:index')
