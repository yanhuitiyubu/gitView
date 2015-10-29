# -*- coding: utf-8 -*-

from io import BytesIO
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from datacollector import DataCollector


__all__ = [
    'PdfReport'
]


class PdfReport(object):

    location = 0
    startLocation = 11

    def __init__(self):
        self.buffer = BytesIO()
        self.pdf = Canvas(self.buffer)

    def basicReport(self, branchIdList, developerIdList, dateRange):
        dataCollector = DataCollector(branchIdList, developerIdList, dateRange)
        title = "GIT VIEW TEAM DATA REPORT"
        subtitle = '_'.join([
            dateRange[0].strftime("%Y.%m.%d"),
            dateRange[1].strftime("%Y.%m.%d")
        ])

        self.__cover(title, subtitle)
        self.pdf.showPage()
        self.location = self.startLocation
        self.__singleLayer(
            'Developers Data',
            dataCollector.developerDataBrief()
        )
        self.__doubleLayer(
            'Branches Data',
            dataCollector.branchData()
        )
        self.__tribleLayer(
            'Developers Data in Projects',
            dataCollector.developerDataVerbose()
        )
        self.pdf.showPage()
        self.pdf.save()
        report = self.buffer.getvalue()
        self.buffer.close()
        return report

    def tagReport(self, branchIdList, developerIdList, tagRange):
        dateRange = (
            min(tagRange[0].submit_date, tagRange[1].submit_date),
            max(tagRange[0].submit_date, tagRange[1].submit_date)
        )
        dataCollector = DataCollector(branchIdList, developerIdList, dateRange)
        title = "GIT VIEW TAG DATA REPORT"
        subtitle = '%s %s to %s %s' % (
            tagRange[0].project.name,
            tagRange[0].name,
            tagRange[1].project.name,
            tagRange[1].name
        )
        self.__cover(title, subtitle)
        self.pdf.showPage()
        self.location = self.startLocation
        self.__singleLayer(
            'Developers Data',
            dataCollector.developerDataBrief()
        )
        self.__doubleLayer(
            'Branches Data',
            dataCollector.branchData()
        )
        self.__tribleLayer(
            'Developers Data in Projects',
            dataCollector.developerDataVerbose()
        )
        self.pdf.showPage()
        self.pdf.save()
        report = self.buffer.getvalue()
        self.buffer.close()
        return report

    def __cover(self, title, subtitle):

        self.pdf.setFont("Helvetica-Bold", 17.5)
        self.pdf.drawString(2.2*inch, 9*inch, title)
        self.pdf.setFont("Helvetica", 10.5)
        self.pdf.drawString(3.2*inch, 8.5*inch, subtitle)

    def __head(self, headtext):
        self.pdf.showPage()
        self.pdf.setFont("Helvetica-Bold", 11.5)
        self.pdf.drawString(1*inch, 10.5*inch, headtext)
        self.pdf.rect(1*inch, 10.3*inch, 6.5*inch, 0.12*inch, fill=1)
        self.location = 10

    def __singleLayer(self, title, args):
        self.__sectionHead(title)
        data = args[0]
        for developer in data:
            self.location -= 0.15
            self.__checkBottom(title)
            self.pdf.setFont("Helvetica-Bold", 9)
            self.pdf.drawString(1*inch, self.location*inch,
                                developer.kerb_name)
            self.__drawLineDataWithPer(data[developer], args[1])
        self.location -= 0.5

    def __doubleLayer(self, title, data):
        self.__sectionHead(title)
        for project in data:
            branchData = data[project]
            self.location -= 0.15
            self.__checkBottom(title)
            self.pdf.setFont("Helvetica", 9)
            self.pdf.drawString(1*inch, self.location*inch, project.name)
            self.location -= 0.15
            for branchItem in branchData:
                self.__checkBottom(title)
                for branch in branchItem:
                    self.pdf.setFont("Helvetica-Bold", 9)
                    self.pdf.drawString(1.3*inch, self.location*inch,
                                        branch.name)
                    self.__drawLineData(branchItem[branch])
                self.location -= 0.15
        self.location -= 0.5

    def __tribleLayer(self, title, data):
        self.__sectionHead(title)
        for developer in data:
            projectData = data[developer]
            self.__checkBottom(title)
            self.pdf.setFont("Helvetica", 9)
            self.location -= 0.15
            self.pdf.drawString(1*inch, self.location*inch,
                                developer.kerb_name)
            for project in projectData:
                branchData = projectData[project]
                self.location -= 0.15
                self.__checkBottom(title)
                self.pdf.setFont("Helvetica-Bold", 9)
                self.pdf.drawString(1.3*inch, self.location*inch, project.name)
                for branchItem in branchData:
                    self.__checkBottom(title)
                    self.pdf.setFont("Helvetica-Bold", 9)
                    self.location -= 0.15
                    for branch in branchItem:
                        self.pdf.drawString(1.5*inch, self.location*inch,
                                            branch.name)
                        self.__drawLineData(branchItem[branch])
            self.location -= 0.1
            self.pdf.line(1*inch, self.location*inch,
                          7.5*inch, self.location*inch)
        self.location -= 0.5

    def __drawLineData(self, lineData):
        x_value = 3.8
        self.pdf.drawString(x_value*inch, self.location*inch,
                            str(lineData.commit))
        self.pdf.drawString((x_value+1)*inch, self.location*inch,
                            str(lineData.line))
        self.pdf.drawString((x_value+2)*inch, self.location*inch,
                            str(lineData.added))
        self.pdf.drawString((x_value+3)*inch, self.location*inch,
                            str(lineData.deleted))

    def __drawLineDataWithPer(self, lineData, commitCount):
        x_value = 3.8
        self.pdf.drawString(x_value*inch, self.location*inch,
                            str(lineData.commit))
        self.pdf.drawString(
            (x_value+0.35)*inch,
            self.location*inch,
            "(%.0f%%)" % (float(lineData.commit)/float(commitCount)*100)
        )
        self.pdf.drawString((x_value+1)*inch, self.location*inch,
                            str(lineData.line))
        self.pdf.drawString((x_value+2)*inch, self.location*inch,
                            str(lineData.added))
        self.pdf.drawString((x_value+3)*inch, self.location*inch,
                            str(lineData.deleted))

    def __sectionHead(self, title):
        self.__checkBottom(title)
        self.pdf.setFont("Helvetica-Bold", 11.5)
        self.pdf.drawString(1*inch, self.location*inch, title)
        self.location -= 0.1
        self.pdf.line(1*inch, self.location*inch, 7.5*inch, self.location*inch)
        self.location -= 0.15
        self.pdf.drawString(1*inch, self.location*inch, "Name")
        self.pdf.drawString(3.8*inch, self.location*inch, "Commits")
        self.pdf.drawString(4.8*inch, self.location*inch, "Lines")
        self.pdf.drawString(5.8*inch, self.location*inch, "Added(+)")
        self.pdf.drawString(6.8*inch, self.location*inch, "Deleted(-)")
        self.location -= 0.25
        self.__checkBottom(title)

    def __checkBottom(self, title):
        if self.location <= 1.5:
            self.pdf.showPage()
            self.location = self.startLocation
            self.__sectionHead(title)
