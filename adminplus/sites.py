from django.contrib.admin.sites import AdminSite
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _


class AdminPlusMixin(object):
    """Mixin for AdminSite to allow registering custom admin views."""

    index_template = 'adminplus/index.html'  # That was easy.

    def __init__(self, *args, **kwargs):
        self.custom_views = []
        return super(AdminPlusMixin, self).__init__(*args, **kwargs)

    def register_view(self, path, name=None, urlname=None, visible=True,
                      view=None, app=None):
        """Add a custom admin view. Can be used as a function or a decorator.

        * `path` is the path in the admin where the view will live, e.g.
            http://example.com/admin/somepath
        * `name` is an optional pretty name for the list of custom views. If
            empty, we'll guess based on view.__name__.
        * `urlname` is an optional parameter to be able to call the view with a
            redirect() or reverse()
        * `visible` is a boolean to set if the custom view should be visible in
            the admin dashboard or not.
        * `view` is any view function you can imagine.
        * `app` is how you want to name the app that hold custom views.
        """
        if view is not None:
            self.custom_views.append((path, view, name, urlname, visible, app))
            return

        def decorator(fn):
            self.custom_views.append((path, fn, name, urlname, visible, app))
            return fn
        return decorator

    def get_urls(self):
        """Add our custom views to the admin urlconf."""
        urls = super(AdminPlusMixin, self).get_urls()
        from django.conf.urls import patterns, url
        for path, view, name, urlname, visible, app in self.custom_views:
            urls = patterns(
                '',
                url(r'^%s$' % path, self.admin_view(view), name=urlname),
            ) + urls
        return urls

    def index(self, request, extra_context=None):
        """Make sure our list of custom views is on the index page."""
        ret = super(AdminPlusMixin, self).index(request, extra_context)
        ret.context_data

        app_dict = {}
        for path, view, name, urlname, visible, app in self.custom_views:
            if visible is True:
                name = name or capfirst(view.__name__)
                app  = unicode(app or _('Custom Views'))

                app_dict.setdefault(app, {
                    'app_label': app,
                    'app_url': None,
                    'has_module_perms': True,
                    'models': [],
                    'name': capfirst(app)
                })
                app_dict[app]['models'].append({
                    'add_url': None,
                    'admin_url': path,
                    'name': name,
                    'object_name': 'custom-link',
                    'perms': {'add': None,
                                'change': False,
                                'delete': None},
                })
        
        app_list = ret.context_data.get('app_list', [])
        for app in app_list:
            app_label  = app.get('app_label')
            custom_app = app_dict.get(app_label)
            if custom_app:
                app['models'] = app.get('models', []) + custom_app.get('models')
                app['models'].sort(key=lambda x: x['name'])
                app_dict.pop(app_label)

        ret.context_data['app_list'] = app_list + app_dict.values()

        return ret


class AdminSitePlus(AdminPlusMixin, AdminSite):
    """A Django AdminSite with the AdminPlusMixin to allow registering custom
    views not connected to models."""
