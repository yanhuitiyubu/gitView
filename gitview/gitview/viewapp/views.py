# -*- coding: utf-8 -*-

import itertools
import json
import os
import pdfreport

from datetime import datetime
from datetime import timedelta

from django.db import connection
from django.db.models import Count
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from viewapp.models import Branch
from viewapp.models import Commit
from viewapp.models import Developer
from viewapp.models import DeveloperBranch
from viewapp.models import Project
from viewapp.models import Tag

from logging import getLogger

logger = getLogger("views_logger")


def index(request):
    """Home Page of gitview, show the list of projects and
    developers.

    Query all objects of projects and developers in DB, and
    show on the page.
    """
    project_list = Project.objects.order_by('name')
    author_list = Developer.objects.order_by('full_name')
    args_data = {
        'cv_index': True,
        'project_list': project_list,
        'author_list': author_list
    }
    return render_to_response(
        "viewapp/index.html",
        args_data,
        context_instance=RequestContext(request)
    )


def commit_stat_by_branch(project):
    cursor = connection.cursor()
    sql = '''
select branch_id,
    count(id) as commits_count,
    sum(lines_inserted) as lines_inserted,
    sum(lines_deleted) as lines_deleted,
    sum(lines_inserted) - sum(lines_deleted) as total_lines
from viewapp_commit
where project_id = {0}
group by branch_id'''.format(project.pk)
    cursor.execute(sql)
    result = {}
    while True:
        row = cursor.fetchone()
        if not row:
            break
        result[row[0]] = {
            'commits_count': row[1],
            'lines_inserted': row[2],
            'lines_deleted': row[3],
            'total_lines': row[4],
        }
    return result


def branch_commit_info(project):
    sql = '''
select viewapp_commit.branch_id,
    viewapp_commit.submit_date,
    viewapp_commit.id,
    viewapp_commit.commit_hash
from viewapp_commit
inner join (
    SELECT "viewapp_commit"."branch_id",
       MAX("viewapp_commit"."id") AS "max_commit_pk"
    FROM "viewapp_commit"
    WHERE "viewapp_commit"."project_id" = {0}
    GROUP BY "viewapp_commit"."branch_id") as t1
on viewapp_commit.id = t1.max_commit_pk
'''.format(project.pk)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    while True:
        row = cursor.fetchone()
        if not row:
            break
        result[row[0]] = {
            'commit_id': row[2],
            'commit_hash': row[3],
            'submit_date': row[1],
        }
    return result


def project_report(request, project_id):
    '''Overview of one project.

    List branchs of project, visitor can get general data of every branch.
    '''
    project = get_object_or_404(Project, pk=project_id)
    args_data = {'cv_index': True, 'project': project}

    qs = Branch.objects.filter(project=project).values('pk', 'name')
    branches = dict(((branch['name'], branch) for branch in qs.iterator()))
    commit_stat = commit_stat_by_branch(project)
    commit_infos = branch_commit_info(project)

    def _branch_iterator():
        keys = branches.keys()
        keys.sort()
        for key in keys:
            branch = branches[key]
            stat = commit_stat[branch['pk']]
            commit_info = commit_infos[branch['pk']]
            yield branch, stat, commit_info

    args_data.update({
        'branches': _branch_iterator(),
    })

    return render_to_response("viewapp/show.html",
                              args_data,
                              context_instance=RequestContext(request))


@require_GET
def branch_search_show(request):

    dateFrom, dateTo = get_date_range(request)
    project_list = Project.objects.only('pk', 'name')
    branch_list = Branch.objects.only('pk', 'name')
    project_list = Project.objects.only('name', 'pk')
    project_id = request.GET.get('project', None)
    branch_id = request.GET.get('branch', None)

    if project_id:
        branch_list = Branch.objects.filter(
            project=project_id).only('name', 'project__name')
    else:
        branch_list = None

    args_data = {
        'cv_branch_details': True,
        'project_list': project_list,
        'project_id': int(project_id) if project_id else None,
        'branch_list': branch_list,
        'branch_id': int(branch_id) if branch_id else None,
        'dateFrom': dateFrom,
        'dateTo': dateTo,
    }

    search_commits = all((branch_id, dateFrom, dateTo))
    if search_commits:
        branch = get_object_or_404(Branch.objects.only('pk', 'project'),
                                   pk=int(request.GET['branch']))
        date_range = get_date_range(request)
        commits_total = get_commits_total(project=branch.project,
                                          branch=branch,
                                          submit_date__range=date_range)
        is_empty = commits_total['commits_amount'] == 0
        if is_empty:
            commit_list = ()
            commits_total['total_lines'] = None
        else:
            commit_list = get_commits(project=branch.project,
                                      branch=branch,
                                      submit_date__range=date_range)
            commits_total['total_lines'] = commits_total['lines_inserted'] - \
                                           commits_total['lines_deleted']
        args_data.update({
            'commit_list': commit_list,
            'commits_total': commits_total,
        })
    return render_to_response('viewapp/branch_search.html',
                              args_data,
                              context_instance=RequestContext(request))


def get_commits(**kwargs):
    commits = Commit.objects.filter(**kwargs)
    commits = commits.select_related('developer','project__name','project__code_host__commit_url')
    return commits.only('commit_hash', 'submit_date',
                        'summary',
                        'lines_inserted', 'lines_deleted',
                        'total_files', 'developer__full_name',
                        'project__code_host__commit_url',
                        'project__name')

def get_commits_total(**kwargs):
    qs = Commit.objects.filter(**kwargs)
    return qs.aggregate(commits_amount=Count('pk'),
                        lines_inserted=Sum('lines_inserted'),
                        lines_deleted=Sum('lines_deleted'))

@require_GET
def author_search(request, author_id):
    author = get_object_or_404(Developer, pk=author_id)
    dateFrom, dateTo = get_date_range(request)
    branch_id = request.GET.get('branch', None)
    project_id = request.GET.get('project', None)
    project_list = author.projects.only('name', 'pk')
    branch_list = None
    if project_id:
        branch_list = Branch.objects.filter(
            project__pk=project_id).only('pk', 'name')

    args_data = {
        'cv_index': True,
        'dateFrom': dateFrom,
        'dateTo': dateTo,
        'project_id': int(project_id) if project_id else None,
        'project_list': project_list,
        'branch_id': int(branch_id) if branch_id else None,
        'branch_list': branch_list if branch_list else None,
        'author': author
    }
    search_commits = all((project_id, branch_id, dateFrom, dateTo))
    if search_commits:
        commits_total = get_commits_total(branch=int(branch_id),
                                          developer=author_id,
                                          submit_date__range=(dateFrom, dateTo))
        is_empty = commits_total['commits_amount'] == 0
        if is_empty:
            commit_list = ()
            commits_total['total_lines'] = None
        else:
            commit_list = get_commits(branch=int(branch_id),
                                      developer=author_id,
                                      submit_date__range=(dateFrom, dateTo))
            commits_total['total_lines'] = commits_total['lines_inserted'] - \
                                           commits_total['lines_deleted']
        args_data.update({
            'commit_list': commit_list,
            'commits_total': commits_total,
        })
    return render_to_response(
        "viewapp/developer_search.html",
        args_data,
        context_instance=RequestContext(request)
    )


# interim report page
def interim_report_toweb(request):
    """Iterim report.

    When date given, report of the day, the week and the month before
    the date will be showed.
    """
    selected_date = datetime.today()
    args_data = {'cv_interim_report': True}

    if 'dateSelect' in request.GET:
        try:
            selected_date = datetime.strptime(request.GET['dateSelect'],
                                              '%Y-%m-%d')
            (day_projects,
             day_developers,
             day_from,
             day_to) = day_report(selected_date)
            (week_projects,
             week_developers,
             week_from,
             week_to) = week_report(selected_date)
            (month_projects,
             month_developers,
             month_from,
             month_to) = month_report(selected_date)

            # Get related projects' name and calculate total lines
            project_pks = [item['project'] for item in itertools.chain(
                day_projects, week_projects, month_projects)]
            qs = Project.objects.filter(pk__in=project_pks).values('pk',
                                                                   'name')
            projects = dict(((row['pk'], row['name'])
                              for row in qs.iterator()))
            for stat in itertools.chain(day_projects,
                                        week_projects,
                                        month_projects):
                stat['project_name'] = projects[stat['project']]
                stat['total_lines'] = stat['lines_inserted'] - stat['lines_deleted']

            # Get related developers' name and email and calculate total lines
            developer_pks = [item['developer'] for item in itertools.chain(
                day_developers, week_developers, month_developers)]
            qs = Developer.objects.filter(pk__in=developer_pks).values(
                'pk', 'full_name', 'email')
            developers = dict(((row['pk'], {'full_name': row['full_name'],
                                            'email': row['email']})
                                for row in qs.iterator()))
            for stat in itertools.chain(day_developers,
                                        week_developers,
                                        month_developers):
                stat['info'] = developers[stat['developer']]
                stat['total_lines'] = stat['lines_inserted'] - stat['lines_deleted']

            args_data.update({
                'dateSelect': selected_date,
                'day_from': day_from,
                'day_to': day_to,
                'day_projects_list': day_projects,
                'day_developers_list': day_developers,
                'week_from': week_from,
                'week_to': week_to,
                'week_projects_list': week_projects,
                'week_developers_list': week_developers,
                'month_from': month_from,
                'month_to': month_to,
                'month_projects_list': month_projects,
                'month_developers_list': month_developers,
            })
            return render_to_response(
                "viewapp/interim_report.html",
                args_data,
                context_instance=RequestContext(request)
            )
        except Exception as error:
            logger.error(error)
            args_data.update({
              'dateSelect': selected_date,
            })
            return render_to_response(
                "viewapp/interim_report.html",
                args_data,
                context_instance=RequestContext(request)
            )
    else:
        args_data.update({
          'dateSelect': selected_date,
        })
        return render_to_response(
            "viewapp/interim_report.html",
            args_data,
            context_instance=RequestContext(request)
        )


def team_report(request):
    """Team report.

    This moudule can give PDF report of several projects and developers.
    """
    project_all = Project.objects.order_by('name')
    developer_all = Developer.objects.order_by('full_name')
    branch_all = Branch.objects.order_by('name')
    args_data = {'cv_team_report': True}

    project_list = [
        dict(key=project.id,
             text=project.name,
             values=[dict(key=branch.id, text=branch.name)
                     for branch in project.branches.iterator()])
        for project in project_all]

    developer_list = [
        dict(key=developer.pk, text=u'{0} &lt;{1}&gt;'.format(developer.full_name,
                                                       developer.email))
        for developer in developer_all.iterator()]

    branch_to_developer = {}
    developer_to_branch = {}
    developer_branch_rels = DeveloperBranch.objects.order_by('branch',
                                                             'developer')
    for rel in developer_branch_rels.iterator():
        l = branch_to_developer.get(rel.branch_id, None)
        if l is None:
            branch_to_developer[rel.branch_id] = [rel.developer_id]
        else:
            l.append(rel.developer_id)

        l = developer_to_branch.get(rel.developer_id, None)
        if l is None:
            developer_to_branch[rel.developer_id] = [rel.branch_id]
        else:
            l.append(rel.branch_id)

    dateFrom, dateTo = get_date_range(request)
    if (dateFrom < dateTo and "subprojects" in request.GET and
            "developers" in request.GET):
        timetext = '_'.join([
            dateFrom.strftime("%Y.%m.%d"),
            dateTo.strftime("%Y.%m.%d")
        ])
        filename = '_'.join([timetext, 'gitview.pdf'])
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        report = pdfreport.PdfReport()
        response.write(report.basicReport(
            request.GET.getlist('subprojects'),
            request.GET.getlist('developers'),
            (dateFrom, dateTo)
        ))
        return response
    else:
        args_data.update({
            'dateFrom': dateFrom,
            'dateTo': dateTo,
            'project_list': json.dumps(project_list),
            'developer_list': json.dumps(developer_list),
            'branch_developer': json.dumps(branch_to_developer),
            'developer_branch': json.dumps(developer_to_branch),
        })
        return render_to_response(
            "viewapp/team_report.html",
            args_data,
            context_instance=RequestContext(request)
        )


def tag_report(request):
    project_all = Project.objects.order_by('name')
    developer_all = Developer.objects.order_by('full_name')
    branch_all = Branch.objects.order_by('name')
    args_data = {'cv_tag_report': True}

    project_list = [
        dict(key=project.pk,
             text=project.name,
             values=[dict(key=branch.pk, text=branch.name)
                     for branch in project.branches.iterator()])
        for project in project_all.iterator()]

    developer_list = [
        dict(key=developer.pk,
             text=u"{0} &lt;{1}&gt;".format(developer.full_name, developer.email))
        for developer in developer_all.iterator()]

    branch_to_developer = {}
    developer_to_branch = {}
    developer_branch_rels = DeveloperBranch.objects.order_by('branch',
                                                             'developer')
    for rel in developer_branch_rels.iterator():
        l = branch_to_developer.get(rel.branch_id, None)
        if l is None:
            branch_to_developer[rel.branch_id] = [rel.developer_id]
        else:
            l.append(rel.developer_id)

        l = developer_to_branch.get(rel.developer_id, None)
        if l is None:
            developer_to_branch[rel.developer_id] = [rel.branch_id]
        else:
            l.append(rel.branch_id)

    tag_all = Tag.objects.all()
    tag_list = [dict(key=tag.id, text=tag.name) for tag in tag_all.iterator()]

    branch_to_tags = {}
    qs = Branch.objects.values('pk', 'tags__pk')
    for row in qs.iterator():
        branch_pk = row['pk']
        l = branch_to_tags.get(branch_pk, None)
        if l is None:
            branch_to_tags[branch_pk] = [row['tags__pk']]
        else:
            l.append(row['tags__pk'])

    if ('tag1' in request.GET and 'tag2' in request.GET and
            "subprojects" in request.GET and "developers" in request.GET):
        tag1 = Tag.objects.get(id=int(request.GET['tag1']))
        tag2 = Tag.objects.get(id=int(request.GET['tag2']))
        if tag1 != tag2:
            tagtext = '_'.join([tag1.name, tag2.name])
            filename = '_'.join([tagtext, 'gitview.pdf'])
            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = \
                'attachment; filename=%s' % filename
            report = pdfreport.PdfReport()
            response.write(report.tagReport(
                request.GET.getlist('subprojects'),
                request.GET.getlist('developers'),
                (tag1, tag2)
            ))
            return response

    args_data.update({
        'project_list': json.dumps(project_list),
        'developer_list': json.dumps(developer_list),
        'tag_list': json.dumps(tag_list),
        'branch_developer': json.dumps(branch_to_developer),
        'developer_branch': json.dumps(developer_to_branch),
        'branch_tag': json.dumps(branch_to_tags),
    })
    return render_to_response(
        "viewapp/tag_report.html",
        args_data,
        context_instance=RequestContext(request)
    )


def interim_report(date_from, date_to):
    qs = Commit.objects.filter(submit_date__range=(date_from, date_to))

    ret1 = qs.values('project').annotate(
        lines_inserted=Sum('lines_inserted'),
        lines_deleted=Sum('lines_deleted'),
        commits_count=Count('pk'))

    ret2 = qs.values('developer').annotate(
        lines_inserted=Sum('lines_inserted'),
        lines_deleted=Sum('lines_deleted'),
        commits_count=Count('pk'))

    return ret1, ret2


# For interim report
def day_report(d):
    day = d - timedelta(days=1)
    date_range = (datetime(day.year, day.month, day.day, 0, 0, 0),
                  datetime(d.year, d.month, d.day, 0, 0, 0))

    return interim_report(*date_range) + date_range


# For interim report
def week_report(d):
    dayto = d - timedelta(days=d.weekday())
    days = timedelta(days=7)
    dayfrom = dayto - days

    date_range = (datetime(dayfrom.year, dayfrom.month, dayfrom.day, 0, 0, 0),
                  datetime(dayto.year, dayto.month, dayto.day, 0, 0, 0))

    return interim_report(*date_range) + date_range


# For interim report
def month_report(d):
    dayscount = timedelta(days=d.day)
    one_day = timedelta(days=1)
    dayfrom = d - one_day
    dayto = dayfrom + one_day

    date_range = (datetime(dayfrom.year, dayfrom.month, 1, 0, 0, 0),
                  datetime(dayto.year, dayto.month, 1, 0, 0, 0))

    return interim_report(*date_range) + date_range


# inbuild tools
def checkout_branch(project_dir, branch):
    try:
        os.chdir(project_dir)
    except Exception as error:
        logger.error(error)
    cmd = ' '.join(['git checkout', branch])
    try:
        os.system(cmd)
    except Exception as error:
        logger.error(error)


def total_data(commit_list):
    total_data = [0, 0, 0]
    if not commit_list:
        return commit_list
    else:
        for commit in commit_list:
            total_data[0] += commit.lines_inserted
            total_data[1] += commit.lines_deleted
            total_data[2] += commit.total_lines
        return total_data


def patch_type_data(conf, name):
    classification_list = {'REV': 0, 'SQL': 0, 'FIX': 0, 'DOC': 0, 'OTR': 0}
    if conf == 'pro':
        project = Project.objects.get(name=name)
        if project.id:
            commit_list = Commit.objects.filter(project=project)
        if commit_list:
            for commit in commit_list:
                if commit.classification in classification_list:
                    classification_list[commit.classification] += 1
    elif conf == 'dev':
        developer = Developer.objects.get(kerb_name=name)
        if developer.id:
            commit_list = Commit.objects.filter(developer=developer)
        if commit_list:
            for commit in commit_list:
                if commit.classification in classification_list:
                    classification_list[commit.classification] += 1
    return classification_list


def rewrite_templates(report_dir):
    os.chdir(report_dir)
    files = ['index.html', 'activity.html',
             'authors.html', 'files.html', 'lines.html', 'tags.html']
    for template in files:
        with open(template, "r+") as f:
            d = f.read()
            d.replace('gitstats.css', '/static/gitstats.css')
            f.seek(0)
            f.write(d)


def move_templates(out_dir, to_dir):
    os.chdir(out_dir)
    files = ['index.html', 'activity.html',
             'authors.html', 'files.html', 'lines.html', 'tags.html']
    for template in files:
        cmd = ' '.join(['mv', template, to_dir])
        try:
            os.system(cmd)
        except Exception as error:
            logger.error(error)


def get_date_range(request):
    if 'datefrom' in request.GET and 'dateto' in request.GET:
        try:
            dateFromStr = request.GET['datefrom']
            dateToStr = request.GET['dateto']
            dateFrom = datetime.strptime(dateFromStr, '%Y-%m-%d')
            dateTo = datetime.strptime(dateToStr, '%Y-%m-%d')
        except Exception as error:
            logger.error(error)
    else:
        dateFrom = datetime.today()
        dateTo = dateFrom
    return dateFrom, dateTo


@require_GET
@cache_control(max_age=43200)
def get_branches_from_project(request, project_id):
    """Get branch names from a specific project"""
    qs = Branch.objects.filter(project=project_id).values('pk', 'name')
    data = json.dumps(list(qs.iterator()))
    return HttpResponse(data, content_type='application/json')

