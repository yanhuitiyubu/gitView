# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'viewapp.views.index', name='root-index'),
    url(r'', include('viewapp.urls')),
    #url(r'^api-auth/', include('rest_framework.urls',
    #	                  namespace='rest_framework')),
    #Examples:
    #url(r'^$', 'gitview.views.home', name='home'),
    #url(r'^gitview/', include('gitview.foo.urls')),

    #Uncomment the line below to enable admin documentation:
    #url(r'^admin/doc/',
    #include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),)
