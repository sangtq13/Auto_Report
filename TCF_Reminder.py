# -*- coding: utf-8 -*-
import os
import sys
import json
from downloadFromATE import DownloadTestFromATE
from generateToJson import GenerateToJSon
from generateToExcel import GenerateToExcel
from emailSending import EmailSending
from generateReasonDetailToJson import GenerateReasonDetailToJson
reload(sys)
sys.setdefaultencoding('utf8')

class reportFromATE(object):
    """docstring for reportFromATE"""
    def __init__(self):
        super(reportFromATE, self).__init__()
        current_dir = os.path.abspath(os.path.dirname(__file__))
        try:
            file_path = os.path.join(current_dir,'.config\\jira_info.json')
            with open(file_path, 'r') as info_file:
                self.jira_info = json.load(info_file)
                self.list_release_name =self.jira_info["release_name_list"]
                for element in self.list_release_name:
                    print element
        except Exception as error_log:
            raise error_log
            print "Can not open this file %s",error_log
    def run(self):
        for release_name in self.list_release_name:
            print "Starting!!!!"
            # objectDownloadATE = DownloadTestFromATE(release_name)
            # objectDownloadATE.DownloadReport()
            # objectDownloadATE.UnzipReportFile()
            objectGenJson = GenerateToJSon(release_name)
            objectGenJson1 = GenerateReasonDetailToJson(release_name)            
            list_module = objectGenJson.GetListAllModule()
            for module in list_module:
                error = objectGenJson1.AF_GenAllModuleReportToJson(release_name, module)

            list_error_log = []
            for module in list_module:
                list_error_log += objectGenJson.GenModuleReportToJson(module)
            if list_error_log:
                print "\n------------ List not available report ------------"
            else:
                print "Nothing module got err!!!"
            list_merge_cell_total = []
            list_work_sheet = []
            objectSumarySheet = GenerateToExcel(release_name)
            list_work_sheet.append(objectSumarySheet.excel_current_sheet_name)
            list_merge_cell_total.append(objectSumarySheet.LoadWorkSheet())
            objectSumarySheet.MakeUpdateMergeCell(list_work_sheet, list_merge_cell_total)
            objectEmail = EmailSending(release_name)
            objectEmail.run()
if __name__ == '__main__':
    objectReportATE = reportFromATE()
    objectReportATE.run()

        