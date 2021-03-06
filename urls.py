from django.conf.urls.defaults import *
import django.contrib.auth.views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #general
    (r'^$', 'addons.main.views.index'),
    (r'^login/$', 'addons.main.views.login_user'),
    (r'^registration/$', 'addons.main.views.register'),
    #(r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'django.contrib.auth.views.logout'),

    #thats should be removed in production use
    (r'^stuff/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/kkszysiu/code/git/addons/stuff/'}),

    #comments
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^comments/post/', 'addons.main.views.comment_post_wrapper'),
    (r'^comments/posted/(.*)', 'addons.main.views.comment_posted'),

    #categories
    (r'^category/(?P<id>[0-9]+)/$', 'addons.main.views.show_category'),
    (r'^category/(?P<id>[0-9]+)/(?P<sortby>.*)/$', 'addons.main.views.show_category'),

    #tags
    (r'^tag/(.*)/$', 'addons.main.views.show_addons_by_tag'),

    #addons
    (r'^addon/my/$', 'addons.main.views.my_addons'),
    (r'^addon/add/$', 'addons.main.views.add_addon'),
    (r'^addon/(?P<id>[0-9]+)/edit/$', 'addons.main.views.edit_addon'),
    (r'^addon/(?P<id>[0-9]+)/add_screenshot/$', 'addons.main.views.add_screenshot'),
    (r'^addon/(?P<addon_id>[0-9]+)/delete_screenshots/$', 'addons.main.views.delete_screenshots'),
    (r'^addon/(?P<addon_id>[0-9]+)/delete_screenshot/(?P<screenshot_id>[0-9]+)/$', 'addons.main.views.delete_screenshot'),
    (r'^addon/(?P<id>[0-9]+)/add_version/$', 'addons.main.views.add_version'),
    (r'^addon/(?P<addon_id>[0-9]+)/delete_version/(?P<version_id>[0-9]+)/$', 'addons.main.views.delete_version'),
    (r'^addon/(?P<id>[0-9]+)/$', 'addons.main.views.show_addon'),
    (r'^addon/(?P<id>[0-9]+)/download/(?P<version_id>[0-9]+)/$', 'addons.main.views.download_addon'),

    # Example:
    # (r'^addons/', include('addons.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
