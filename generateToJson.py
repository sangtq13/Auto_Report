import os
import sys
import getopt
import pprint
from collections import OrderedDict
import json
from jira import JIRA
import requests
import tarfile
import zipfile
import shutil
import re
from datetime import datetime
from bs4 import BeautifulSoup

from configManagmentInterface import ConfigManagmentInterface
reload(sys)
sys.setdefaultencoding('utf8')

class GenerateToJSon(ConfigManagmentInterface):
    """docstring for GenerateToJSon
    Task:
        Put all the results to JSON file
        Input Dir :  current_dir\[Release_Name]\Derivatives eg: .\S32K14X_RTM_2.0.0\S32K142
        Output Dir : \.config\[Release_Name]\[Date_and_Time] eg:.config\S32K14X_RTM_2.0.0\20180615_09_13
            + List test cases failed for each compilers
            + List number of test cases on ATE
            + List SRS covered
    """
    def __init__(self,p_release_name):
        super(GenerateToJSon, self).__init__(p_release_name)

    def AF_GetSrsCover(self, file, module_report_info):
        with open(file, 'r') as file_object:
            file_data = file_object.readlines()
            for line in file_data:
                if self.tm_key_word in line:
                    percentage = int(round(float(''.join(re.findall("\d+\.\d+", line)))))
                    module_report_info = percentage

        return module_report_info


    def GenJson(self, file_path, input_dict):
        with open(file_path, 'w') as file:
            json.dump(input_dict, file, sort_keys=True, indent=4)


    def AF_GetSummaryReportInfo(self, file, module_report_info, f_list_test_fail, f_module_name):
        module_report_info["number_of_test_id"]      = 0
        module_report_info["number_of_test_na"]      = 0
        module_report_info["number_of_test_fail"]    = 0
        module_report_info["number_of_test_id_fail"] = 0

        with open(file, 'r') as html_object:
            raw_html = BeautifulSoup(html_object, 'html.parser')

        list_table = raw_html.find_all("table")

        found_table = False
        for table_item in list_table:
            column_list = table_item.find_all('th')
            for item in column_list:
                if "Test ID" in item.contents:
                    get_table_data = table_item
                    found_table = True
                    break
            if found_table is True:
                break

        if found_table is True:
            # get list column
            column_list = get_table_data.find_all('th')
            list_column_name = []
            for item in column_list:
                list_column_name.append(str(''.join(item.contents)))

            test_id_column_index = 0

            # remove the first row header to calculate number of test_id
            table_row = get_table_data.find_all('tr')[1:]

            # find list test case uses more than 1 test suite/test configuration
            list_test_case_duplicate = []
            list_all_test_id = []
            for row in table_row:
                column_list = row.find_all('td')
                test_id = str(''.join(column_list[0].contents))
                if test_id not in list_all_test_id:
                    list_all_test_id.append(test_id)
                else:
                    list_test_case_duplicate.append(test_id)

            number_of_test_id       = len(table_row)
            number_of_test_id_fail  = 0
            number_of_test_fail     = 0
            number_of_test_na       = 0
            for row in table_row:
                column_list = row.find_all('td')
                test_id = str(''.join(column_list[0].contents))
                cfg_id = ""
                if test_id in list_test_case_duplicate:
                    cfg_id = str(''.join(column_list[2].contents)).replace(f_module_name.lower(), "")
                test_cfg_id = test_id + cfg_id
                module_report_info[test_cfg_id] = {}
                fail_detect = False

                for index in range(len(column_list)):
                    if "FAIL" in column_list[index].contents:
                        # test_id, compiler name
                        module_report_info[test_cfg_id][list_column_name[index]] = "FAIL"
                        number_of_test_fail += 1
                        fail_detect = True
                        if test_cfg_id not in f_list_test_fail:
                            f_list_test_fail.append(test_cfg_id)
                    if "N/A" in column_list[index].contents:
                        number_of_test_na   += 1
                        module_report_info[test_cfg_id][list_column_name[index]] = "N/A"
                if fail_detect is True:
                    number_of_test_id_fail += 1

                # remove test case pass from dict
                is_test_id_pass = bool(module_report_info[test_cfg_id])
                if is_test_id_pass is False:
                    module_report_info.pop(test_cfg_id, None)

            module_report_info["number_of_test_id"]      = number_of_test_id
            module_report_info["number_of_test_na"]      = number_of_test_na
            module_report_info["number_of_test_fail"]    = number_of_test_fail
            module_report_info["number_of_test_id_fail"] = number_of_test_id_fail

        return module_report_info, f_list_test_fail


    def GenModuleReportToJson(self, module_name):
        report_dir          = self.download_folder_name
        tm_template_name    = self.template_tm_name
        list_error_log      = []

        tm_report_dir       = report_dir.replace("REPORT_NAME", self.tm_report_folder)
        summary_report_dir  = report_dir.replace("REPORT_NAME", self.summary_report_folder)
        module_info = dict([(key, {}) for key in self.list_derivative])

        list_tc_fail = []
        for derivetive in self.list_derivative:
            module_info[derivetive]["number_of_test_id"]        = "N/A"
            module_info[derivetive]["number_of_test_id_fail"]   = "N/A"
            module_info[derivetive]["number_of_test_na"]        = "N/A"
            module_info[derivetive]["number_of_test_id"]        = "N/A"
            module_info[derivetive]["srs_coverage"]             = "N/A"
            module_info[derivetive]["preliminary_srs_coverage"] = "N/A"

            report_html_file = os.path.join(summary_report_dir.replace('DERIVATIVE', derivetive), self.template_summary_name.replace('DERIVATIVE', derivetive).replace('MODULE', module_name.upper()))
            if os.path.exists(report_html_file):
                module_info[derivetive], list_tc_fail = self.AF_GetSummaryReportInfo(report_html_file, module_info[derivetive], list_tc_fail, module_name)
            else:
                list_error_log.append(report_html_file)

            report_tm_log_file = os.path.join(tm_report_dir.replace('DERIVATIVE', derivetive), tm_template_name.replace('DERIVATIVE', derivetive).replace('MODULE', module_name.lower()))
            if os.path.exists(report_tm_log_file):
                module_info[derivetive]["srs_coverage"] = self.AF_GetSrsCover(report_tm_log_file, module_info[derivetive]["srs_coverage"])
            else:
                list_error_log.append(report_tm_log_file)

            tm_template_name = self.tm_report_temporary_name
            report_tm_log_file = os.path.join(tm_report_dir.replace('DERIVATIVE', derivetive), tm_template_name.replace('DERIVATIVE', derivetive).replace('MODULE', module_name.lower()))
            if os.path.exists(report_tm_log_file):
                module_info[derivetive]["preliminary_srs_coverage"] = self.AF_GetSrsCover(report_tm_log_file, module_info[derivetive]["preliminary_srs_coverage"])
            else:
                list_error_log.append(report_tm_log_file)

        if list_tc_fail:
            module_info[self.module_key_fail] = list_tc_fail
        else:
            module_info[self.module_key_fail] = []

        if self.date_time_download == 0:
            self.date_time_download = self.GetCurrentDateTime()
        if not os.path.exists(self.current_report_json + self.date_time_download):
            os.makedirs(self.current_report_json + self.date_time_download)
        json_path = self.current_report_json + self.date_time_download + "\\" + module_name.upper() + ".json"
        self.GenJson(json_path, module_info)
        return list_error_log