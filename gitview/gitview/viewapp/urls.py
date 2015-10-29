#!/usr/bin/env python
# coding=utf-8

from django.conf.urls import patterns,  url

from viewapp import views

urlpatterns = patterns('',
    #url(r'^index$', views.index, name='index'),
    url(r'^$', views.index, name='index'),
    url(r'^authors/(?P<author_id>\d+)/$', views.author_search, name='authors'),
    url(r'^branches/$', views.branch_search_show, name='branches'),
    url(r'^projects/(?P<project_id>\d+)/$', views.project_report, name='projects'),
    url(r'^report/interim/$', views.interim_report_toweb, name='report-interim'),
    url(r'^report/tag/$', views.tag_report, name='report-tag'),
    url(r'^report/team/$', views.team_report, name='report-team'),
    url(r'^projects/(?P<project_id>\d+)/branches/$', views.get_branches_from_project, name='project-branches'),
)
