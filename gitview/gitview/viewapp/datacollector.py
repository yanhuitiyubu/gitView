# -*- coding: utf-8 -*-

from viewapp.models import Commit

__all__ = [
    'LineData',
    'DataCollector'
]


class LineData(object):

    def __init__(self, commit=0, line=0, added=0, deleted=0):
        self.commit = commit
        self.line = line
        self.added = added
        self.deleted = deleted

    def __add__(self, other):
        temp = LineData(
            self.commit + other.commit,
            self.line + other.line,
            self.added + other.added,
            self.deleted + other.deleted
        )
        return temp

    def __iadd__(self, other):
        self = self.__add__(other)
        return self

    def __lt__(self, other):
        return self.commit < other.commit


class DataCollector(object):

    def __init__(self, branchIdList, developerIdList, dateRange):
        self.rawData = Commit.objects.filter(
            branch_id__in=branchIdList,
            developer_id__in=developerIdList,
            submit_date__range=dateRange
        )

    def developerDataBrief(self):
#         return rawToDeveloper(self.rawData)
        developerData = {}
        developerSplit = rawSplitDeveloper(self.rawData)
        commitCount = 0
        for developer in developerSplit:
            developerUnit = \
                proAddUp(branchMerge(rawToBranch(developerSplit[developer])))
            developerData[developer] = developerUnit
            commitCount += developerUnit.commit
        return developerData, commitCount

    def developerDataVerbose(self):
        devProBranData = {}
        developerSplit = rawSplitDeveloper(self.rawData)
        for developer in developerSplit:
            devProBranData[developer] = \
                branchSplitProject(rawToBranch(developerSplit[developer]))
        return devProBranData

    def branchData(self):
        return branchSplitProject(rawToBranch(self.rawData))


def extractData(patch):
    return LineData(1, patch.total_lines,
                    patch.lines_inserted, patch.lines_deleted)


def rawToDeveloper(rawData):
    developerData = {}
    for patch in rawData:
        developerData[patch.developer] = extractData(patch) + \
            developerData.get(patch.developer, LineData())
    return developerData


def rawToBranch(rawData):
    branchData = {}
    for patch in rawData:
        branchData[patch.branch] = extractData(patch) + \
            branchData.get(patch.branch, LineData())
    return branchData


def rawSplitDeveloper(rawData):
    developerSplit = {}
    for patch in rawData:
        developerSplit.setdefault(patch.developer, []).append(patch)
    return developerSplit


def branchSplitProject(branchData):
    projectSplit = {}
    for kb in branchData:
        projectSplit.setdefault(kb.project, []).append({kb: branchData[kb]})
    return projectSplit


def branchMerge(branchData):
    projectData = {}
    for kb in branchData:
        if (kb.project not in projectData or
                projectData[kb.project] < branchData[kb]):
            projectData[kb.project] = branchData[kb]
    return projectData


def proAddUp(projectData):
    result = LineData()
    for kp in projectData:
        result += projectData[kp]
    return result
