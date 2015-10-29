# -*- coding: utf-8 -*-

from django.contrib import admin

from viewapp import models


class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project__name',)
    ordering = ('project__name',)
    list_per_page = 50

    def queryset(self, request):
        qs = super(BranchAdmin, self).queryset(request)
        return qs.only('name', 'project__name')
admin.site.register(models.Branch, BranchAdmin)

class CodeHostAdmin(admin.ModelAdmin):
    list_display = ('name','commit_url')

    def queryset(self,request):
        qs = super(CodeHostAdmin,self).queryset(request)
        return qs.only('name','commit_url')
admin.site.register(models.CodeHost, CodeHostAdmin)


class CommitAdmin(admin.ModelAdmin):
    list_display = ('abbreviated_commit_hash', 'submit_date', 'summary',
                    'files_changed', 'lines_inserted', 'lines_deleted',
                    'developer', 'branch')
    list_filter = ('project__name', 'branch__name',)
    ordering = ('-submit_date',)
    list_per_page = 50

    def queryset(self, request):
        qs = super(CommitAdmin, self).queryset(request)
        return qs.only('commit_hash', 'submit_date', 'summary', 'total_files',
                       'lines_inserted', 'lines_deleted',
                       'developer__full_name', 'branch__name')
admin.site.register(models.Commit, CommitAdmin)


class DeveloperAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email')
    ordering = ('full_name',)
    list_per_page = 50
admin.site.register(models.Developer, DeveloperAdmin)


admin.site.register(models.Patch)


class ProjectAdmin(admin.ModelAdmin):
    fields = ('url', 'description','code_host')
    list_display = ('name', 'url', 'being_syncing', 'get_last_synced_on')
    ordering = ('name',)

    def get_last_synced_on(self, obj):
        return '' if obj.last_synced_on is None else obj.last_synced_on
    get_last_synced_on.short_description = 'Last Synced on'
admin.site.register(models.Project, ProjectAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'submit_date', 'project')
    list_filter = ('project__name',)
    ordering = ('name',)
    list_per_page = 50

    def queryset(self, request):
        qs = super(TagAdmin, self).queryset(request)
        return qs.only('name', 'submit_date', 'project__name')
admin.site.register(models.Tag, TagAdmin)


admin.site.register(models.ViewappLog)
