from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from djblets.siteconfig.views import site_settings as djblets_site_settings

from reviewboard.admin.checks import check_updates_required
from reviewboard.admin.cache_stats import get_cache_stats, get_has_cache_stats
from reviewboard.reviews.models import Group, DefaultReviewer
from reviewboard.scmtools.models import Repository
from reviewboard.scmtools import sshutils


@staff_member_required
def dashboard(request, template_name="admin/dashboard.html"):
    """
    Displays the administration dashboard, containing news updates and
    useful administration tasks.
    """
    return render_to_response(template_name, RequestContext(request, {
        'user_count': User.objects.count(),
        'reviewgroup_count': Group.objects.count(),
        'defaultreviewer_count': DefaultReviewer.objects.count(),
        'repository_count': Repository.objects.accessible(request.user).count(),
        'has_cache_stats': get_has_cache_stats(),
        'title': _("Dashboard"),
        'root_path': settings.SITE_ROOT + "admin/db/"
    }))


@staff_member_required
def cache_stats(request, template_name="admin/cache_stats.html"):
    """
    Displays statistics on the cache. This includes such pieces of
    information as memory used, cache misses, and uptime.
    """
    cache_stats = get_cache_stats()

    return render_to_response(template_name, RequestContext(request, {
        'cache_hosts': cache_stats,
        'cache_backend': cache.__module__,
        'title': _("Server Cache"),
        'root_path': settings.SITE_ROOT + "admin/db/"
    }))


@staff_member_required
def site_settings(request, form_class,
                  template_name="siteconfig/settings.html"):
    return djblets_site_settings(request, form_class, template_name, {
        'root_path': settings.SITE_ROOT + "admin/db/"
    })


@staff_member_required
def ssh_settings(request, template_name='admin/ssh_settings.html'):
    key = sshutils.get_user_key()
    error = None

    if request.method == 'POST' and 'generate-key' in request.POST and not key:
        try:
            sshutils.generate_user_key()

            return HttpResponseRedirect('.')
        except IOError, e:
            error = _('Unable to write SSH key file: %s') % e
        except Exception, e:
            error = _('Error generating SSH key: %s') % e

    public_key = ''

    if key:
        fingerprint = sshutils.humanize_key(key)
        base64 = key.get_base64()

        # TODO: Move this wrapping logic into a common templatetag.
        for i in range(0, len(base64), 64):
            public_key += base64[i:i + 64] + '\n'
    else:
        fingerprint = None

    return render_to_response(template_name, RequestContext(request, {
        'title': _('SSH Settings'),
        'key': key,
        'fingerprint': fingerprint,
        'public_key': public_key,
        'error': error,
    }))


def manual_updates_required(request,
                            template_name="admin/manual_updates_required.html"):
    """
    Checks for required manual updates and displays informational pages on
    performing the necessary updates.
    """
    updates = check_updates_required()

    return render_to_response(template_name, RequestContext(request, {
        'updates': [render_to_string(template_name,
                                     RequestContext(request, extra_context))
                    for (template_name, extra_context) in updates],
    }))
