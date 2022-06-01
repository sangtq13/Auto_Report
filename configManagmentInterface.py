import os
import sys
import pprint
from collections import OrderedDict
import json
import shutil
import re
from datetime import datetime
from inspect import currentframe, getframeinfo

reload(sys)
sys.setdefaultencoding('utf8')

class ConfigManagmentInterface(object):
    """docstring for ConfigManagmentInterface"""
    def __init__(self, p_release_name):
        super(ConfigManagmentInterface, self).__init__()
        print "Initialize the ConfigManagmentInterface object"
        # Get current directory
        current_dir = os.path.abspath(os.path.dirname(__file__))
        # Get release name 
        self.release_name = p_release_name;
        try:
            file_path = os.path.join(current_dir, '.config\\jira_info.json')
            with open(file_path, 'r') as info_file:
                self.jira_info = json.load(info_file)
                # self.release_name = self.jira_info["release_name"]
                self.email_operator = self.jira_info["email"]
                self.pass_word_operator = self.jira_info["pass_word"]
        except Exception as error_log:
            print error_log
            print 'Fail to import information, please check %s file' % file_path
        # Get list of file which need to download
        try:
            file_path = os.path.join(current_dir, '.config\\' + self.release_name + '\\' + 'report_info.json')
            with open(file_path, 'r') as info_file:
                self.report_info = json.load(info_file)
        except Exception as error_log:
            print error_log
            print 'Fail to import information, please check %s file' % file_path

        self.date_time_download              = 0
        self.list_download_report            = self.report_info['list_download_report']
        self.list_download_derivative        = self.report_info['list_download_derivative']
        self.download_folder_name            = os.path.join(current_dir, self.release_name + "\\" + self.report_info['download_folder_name'])
        self.template_tm_name                = self.report_info['tm_report_template_name']
        self.tm_report_folder                = 'test_tm'
        self.summary_report_folder           = 'test_summary_report'
        self.template_summary_name           = self.report_info['summary_report_template_name']
        self.template_summary_ts_report_name = self.report_info['summary_ts_report_template_name']
        self.tm_key_word                     = self.report_info['tm_key_word']
        self.tm_report_temporary_name        = self.report_info['tm_report_temporary_name']
        self.module_key_fail                 = "list_test_case_fail"
        self.current_report_json             = os.path.join(current_dir, ".config" + "\\" + self.release_name + "\\" + self.report_info['current_report_json'])

        # Get list of derivatives and link webpages: Eg "S32K148": "http://coral.ea.freescale.net/0/project/fileexplorer/RTpcbG9jYWxfMDNcb3V0cHV0XGxvZ3M="
        try:
            file_path = os.path.join(current_dir, '.config\\' + self.release_name + '\\' + "derivative_info.json")
            with open(file_path, 'r') as info_file:
                self.derivative_info = json.load(info_file)
                self.list_derivative = self.derivative_info.keys()
                self.list_derivative.sort()
        except Exception as error_log:
            print error_log
            print 'Fail to import information, please check %s file' % file_path

        # Get list of compiler used on ATE
        try:
            file_path = os.path.join(current_dir, '.config\\' + self.release_name + '\\' + 'ate_info.json')
            with open(file_path, 'r') as info_file:
                self.ate_info = json.load(info_file)
                self.list_compiler_short_name = self.ate_info['list_compiler_short_name']
        except Exception as error_log:
            print error_log
            print 'Fail to import information, please check %s file' % file_path
        # Get list of module and allocation
        try:
            file_path = os.path.join(current_dir, '.config\\' + self.release_name + '\\' + "module_allocate.json")
            with open(file_path, 'r') as info_file:
                # get json to load into an ordereddict
                self.module_allocate = json.load(info_file, object_pairs_hook=OrderedDict)
                self.list_group      = self.module_allocate.keys()
                self.list_group.sort()
        except Exception as error_log:
            print error_log
            print 'Fail to import information, please check %s file' % file_path
        # Get list of emails 
        try :
            file_path  = os.path.join(current_dir, '.config\\' + self.release_name + '\\' + "email_list.json")
            with open(file_path, 'r')  as info_file:
                self.email_list = json.load(info_file,object_pairs_hook=OrderedDict)
        except Exception as error_log:
            print error_log
            print 'Fail to read the email list, please check %s file' %file_path

    def GetCurrentDateTime(self):
        return '{date:%Y%m%d_%H_%M}'.format(date=datetime.now())

    def GetListAllModule(self):
        self.list_all_module = []
        print "List Group: ", self.list_group
        for group_item in self.list_group:
            for member in self.module_allocate[group_item].keys():
                for module in self.module_allocate[group_item][member]:
                    if module not in self.list_all_module:
                        self.list_all_module.append(module)
        self.list_all_module.sort()
        return self.list_all_module
        pass

    def GetLatestReportFolder(self, f_report_dir):
        list_dir = os.walk(str(f_report_dir)).next()[1]
        list_date_time = []

        for dir_name in list_dir:
            # only get not NULL string
            if filter(str.isdigit, dir_name):
                list_date_time.append(int(filter(str.isdigit, dir_name)))
            else:
                list_date_time.append(0)

        return list_dir[list_date_time.index(max(list_date_time))]
    def printWithFileLine(self):
        frameinfo = getframeinfo(currentframe())
        print frameinfo.filename, frameinfo.lineno
        pass
