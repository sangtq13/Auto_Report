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
from urllib2 import urlopen
import threading
import time
import glob
from configManagmentInterface import ConfigManagmentInterface
from enum import Enum

reload(sys)
sys.setdefaultencoding('utf8')

class PathExtension(Enum):
    REASON_DETAIL_FOLDER_EXTENSION = "ReasonFile\\RELEASE_NAME\\DERIVATIVE\\MODULE_NAME\\TEST_TYPE\\COMPILER"
    REASON_WIRING_FOLDER_EXTENSION = "ReasonFile\\RELEASE_NAME\\DERIVATIVE\\MODULE_NAME\\TEST_TYPE"
    REASON_WIRING_FILE_NAME        = "ar_wiring_test_MODULE_NAME_ghs_log"
    REASON_DETAIL_INT_FILE_NAME    = "ar_int_MODULE_NAME_COMPILER_log"
    REASON_DETAIL_EXT_FILE_NAME    = "ar_ext_MODULE_NAME_COMPILER_log"
    WIRING_DOWNLOAD_NAME           = "ar_wiring_test_MODULE_NAME_ghs"
    EXTERNAL_DOWNLOAD_NAME         = "ar_ext_MODULE_NAME_COMPILER"
    INTERNAL_DOWNLOAD_NAME         = "ar_int_MODULE_NAME_COMPILER"
    WIRING_DOWNLOAD_NAME_LOG       = "ar_wiring_test_MODULE_NAME_ghs_log"
    WIRING_DOWNLOAD_HTML_XML       = "ar_wiring_test_MODULE_NAME_ghs_html_xml"
    EXTERNAL_DOWNLOAD_NAME_LOG     = "ar_ext_MODULE_NAME_COMPILER_log"
    INTERNAL_DOWNLOAD_NAME_LOG     = "ar_int_MODULE_NAME_COMPILER_log"
    RUN_CHECK_FILE_PATH_EXTENSION  = "build\\TEST_SUITE\\debug\\run_check.log"
    BUILD_LOG_FILE_PATH_EXTENSION  = "build\\TEST_SUITE\\out\\build.log"
    TEST_SUITE_XML_FOLDER_NAME     = "specific\\PLATFORM\\"
    TEST_SUITE_XML_NAME            = "TEST_SUITE.xml"

class Status(Enum):
    BUILD_FAIL   = "Build fail"
    DO_RUN_ERROR = "Do run error"
    SUCCESS      = "Success"
    UNKNOWN      = "Unknown"

class TestType(Enum):
    WIRING       = "wiring_test"
    INTERNAL     = "internal_test"
    EXTERNAL     = "external_test"

class ReleaseInfo(Enum):
    PLATFORM     = "PLATFORM"
    RELEASE      = "RELEASE_NAME"
    DERIVATIVE   = "DERIVATIVE"
    TEST_SUITE   = "TEST_SUITE"
    REPORT_NAME  = "REPORT_NAME"
    COMPILER     = "COMPILER"
    MODULE_NAME  = "MODULE_NAME"
    TEST_TYPE    = "TEST_TYPE"

class ErrorSign(Enum):
    NOT_OK       = "NOT OK"
    ERROR        = "error"
    FAIL         = "FAIL"
    NA           = "N/A"

class Platform(Enum):
    S32K11X      = "S32K11X"
    S32K14X      = "S32K14X"
    MPC574XG     = "MPC574XG"
    MPC574XP     = "MPC574XP"
    S32RX7X      = "S32RX7X"

class Derivative(Enum):
    S32K116      = "S32K116"
    S32K118      = "S32K118"
    S32K142      = "S32K142"
    S32K144      = "S32K144"
    S32K146      = "S32K146"
    S32K148      = "S32K148"
    MPC5744P     = "MPC5744P"
    MPC5746C     = "MPC5746C"
    MPC5748G     = "MPC5748G"
    S32R274      = "S32R274"
    S32R372      = "S32R372"

class GenerateReasonDetailToJson(ConfigManagmentInterface):
    """docstring for generateReasonDetailToJson
    @author  : Sang Tran Quang
    @email   : sangtran.hust.1311@gmail.com
    @version : 1.0
    @since   : 1/7/2018
    Task:
        Put all the results to JSON file
        Input Dir :
        current_dir\[Release_Name]\Derivatives 
        eg: .\S32K14X_RTM_2.0.0\S32K142 and other fail report from ATE
        Output Dir : 
        + currnt_dir\.config\[Release_Name] is the folder that contains the output of all module
        + List test cases failed and reason detail for each compilers of all module in all release
    """


    def __init__(self,p_release_name):
        super(GenerateReasonDetailToJson, self).__init__(p_release_name)

    ########################################################################################
    # Description : AF_GetListTestSuite is a function that get all test suite of the module#
    #               in each derivative                                                     #
    # Parameter   :                                                                        #
    # derivative is the derivative information                                             #
    # module is the name of module                                                         #
    # Output : Dictionary contains the information about all test suite of the module      #
    #          wiring_test, internal_test, external_test                                   #
    ########################################################################################
    def AF_GetListTestSuite(self, derivative, module):
        test_suite_file_path = ''
        current_dir = os.path.abspath(os.path.dirname(__file__))

        # Determine platform of this module with the in put derivative
        if derivative == Derivative.MPC5746C.value \
        or derivative == Derivative.MPC5748G.value:
            platform = Platform.MPC574XG.value
        elif derivative == Derivative.MPC5744P.value:
            platform = Platform.MPC574XP.value
        elif derivative == Derivative.S32K142.value \
        or derivative == Derivative.S32K144.value \
        or derivative == Derivative.S32K146.value \
        or derivative == Derivative.S32K148.value:
            platform = Platform.S32K14X.value
        elif derivative == Derivative.S32K116.value \
        or derivative == Derivative.S32K118.value:
            platform = Platform.S32K11X.value
        elif derivative == Derivative.S32R274.value \
        or derivative == Derivative.S32R372.value:
            platform = Platform.S32RX7X.value

        # Determine the file path contain test suite information about module
        file_xml_extension = PathExtension.\
        TEST_SUITE_XML_FOLDER_NAME.value.\
        replace(ReleaseInfo.PLATFORM.value, platform) \
        + PathExtension.TEST_SUITE_XML_NAME.value.\
        replace(ReleaseInfo.TEST_SUITE.value, module.lower())

        test_suite_file_path = os.path.join(current_dir, \
            file_xml_extension)

        # Get data of test suite information from file
        with open(test_suite_file_path, 'r') as html_object:
            raw_html = BeautifulSoup(html_object, 'html.parser')

        list_test_suite = {}
        list_test_suite[TestType.WIRING.value] = []
        list_test_suite[TestType.EXTERNAL.value] = []
        list_test_suite[TestType.INTERNAL.value] = []

        list_class = raw_html.find_all("class")

        for item in list_class:
            if item.attrs['name'] == TestType.WIRING.value:
                test_case_wir_name = re.findall\
                ('[A-Z][a-z]*_*[a-zA-Z]*\S*_TS_*[a-z]*_\d*', \
                    str(item), 0)
                list_test_suite[TestType.WIRING.value] = test_case_wir_name
            elif item.attrs['name'] == 'ext':
                test_case_ext_name = re.findall\
                ('[A-Z][a-z]*_*[a-zA-Z]*\S*_TS_*[a-z]*_\d*', \
                    str(item), 0)
                list_test_suite[TestType.EXTERNAL.value] = test_case_ext_name
            elif item.attrs['name'] == 'int':
                test_case_int_name = re.findall\
                ('[A-Z][a-z]*_*[a-zA-Z]*\S*_TS_*[a-z]*_\d*', \
                    str(item), 0)
                list_test_suite[TestType.INTERNAL.value] = test_case_int_name

        return list_test_suite

    ########################################################################################
    # Description : AF_ChangeHtmlFileName is a function that change file name in summary   #
    #               report folder if it is not correct                                     #
    # Parameter   :                                                                        #
    # dirPath is the folder that contains file                                             #
    # derivative is the derivative infomation                                              #
    ########################################################################################
    def AF_ChangeHtmlFileName(self, dirPath, derivative):
        pattern = r'*.html'
        for pathAndFilename in glob.iglob\
        (os.path.join(dirPath, pattern)):
            file_name = os.path.basename(pathAndFilename)
            list_file_name_member = file_name.split("_")
            list_file_name_member[1] = derivative
            file_name_correct = "_".join(list_file_name_member)
            print file_name_correct
            os.rename(pathAndFilename, \
                os.path.join(dirPath, file_name_correct))

    ########################################################################################
    # Description : AF_GetFailReasonFromTSHtml is a function that get failed reasion of    #
    #               test suite from html file parsing in summary report                    #
    # Parameter   :                                                                        #
    # compiler is the compiler that test suite is failed                                   #
    # derivative is the derivative information                                             #
    # test_suite_fail is the name of test suite that have test case fail                   #
    # Output :                                                                             #
    # Dictionary with key is test case name and value is the error reason                  #
    ########################################################################################
    def AF_GetFailReasonFromTSHtml(self, derivative, 
                                compiler, test_suite_fail):
        download_folder  = self.download_folder_name.\
        replace(ReleaseInfo.DERIVATIVE.value, derivative).\
        replace(ReleaseInfo.REPORT_NAME.value, self.summary_report_folder)

        f_list_reason_fail = {}

        # Determine the html report file
        report_test_suite_fail_html_file = os.path.join(download_folder, \
            compiler, test_suite_fail) + '.html'

        with open(report_test_suite_fail_html_file, 'r') as html_object:
            raw_html = BeautifulSoup(html_object, 'html.parser')

        list_table = raw_html.find_all('table')[1:]
        for item in list_table:
            try:
                if item.find('div'):
                    attributes_dictionary = item.find('div').attrs
                    reason_text = item.find('div').get_text()
                    reason_detail = str(''.join(re.findall\
                        ('[A-Z][a-z]*\s[a-z]*\s[a-z]*', reason_text, 0)))
                    reason_id = attributes_dictionary['id']
                    test_case_name = str(''.join(re.findall\
                        ('[A-Z]\S*_*[a-z]*_TC_\d*', reason_id, 0)))
                    f_list_reason_fail[test_case_name] = reason_detail

            except Exception as error_log:
                print error_log

        return f_list_reason_fail

    ########################################################################################
    # Description : AF_GetOtherFailReason is a function that get orther failed reasion of  #
    #               test suite that don't know error reason                                #
    # Parameter   :                                                                        #
    # release_name is release information                                                  #
    # derivative is the derivative infomation                                              #
    # module_name is name of the module                                                    #
    # test_type is type of test suite                                                      #
    # compiler is the compiler that test suite is failed                                   #
    # list_test_suite is a list contain all test suite that don't know error reason        #
    # Output :                                                                             #
    # Dictionary with key is test suite and value is the error reason                      #
    ########################################################################################
    def AF_GetOtherFailReason(self, release_name, derivative, 
                                module_name, test_type, 
                                compiler, list_test_suite):
        af_download_link    = self.derivative_info[derivative]
        af_masterLink       = "/".join(af_download_link.split("/")[0:3])
        af_pageSouce = ''

        # Get link dowmload for list test suite on ATE
        while af_pageSouce == '':
            try:
                af_pageSouce = requests.get(af_download_link).\
                text.encode('utf8')
                af_listPageSourceLine = af_pageSouce.split("\n")
                f_list_reason_fail = {}
                m_downloadLink2 = None

                for line in af_listPageSourceLine:
                    if test_type == TestType.WIRING.value:
                        if PathExtension.WIRING_DOWNLOAD_NAME.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower()) in line:
                            download_master_link = af_masterLink \
                            + line.split("\"")[1]
                            break
                    elif test_type == TestType.EXTERNAL.value:
                        if PathExtension.EXTERNAL_DOWNLOAD_NAME.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                        .replace(ReleaseInfo.COMPILER.value, compiler.lower()) in line:
                            download_master_link = af_masterLink \
                            + line.split("\"")[1]
                            break
                    elif test_type == TestType.INTERNAL.value:
                        if PathExtension.INTERNAL_DOWNLOAD_NAME.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                        .replace(ReleaseInfo.COMPILER.value, compiler.lower()) in line:
                            download_master_link = af_masterLink \
                            + line.split("\"")[1]

                m_reportPageSource = (requests.get(download_master_link).\
                    text.encode('utf8')).split("\n")

                for line in m_reportPageSource:
                    if "downloads" in line:
                        m_downloadLink = af_masterLink + line.split("\"")[1]
                        break

                m_reportPageSource1 = (requests.get(m_downloadLink)\
                    .text.encode('utf8')).split("\n")

                for line in m_reportPageSource1:
                    if test_type == TestType.WIRING.value:
                        if PathExtension.WIRING_DOWNLOAD_HTML_XML.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower()) in line:
                            m_downloadLink2 = af_masterLink + line.split("\"")[1]
                        elif PathExtension.WIRING_DOWNLOAD_NAME_LOG.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower()) in line:
                            m_downloadLink1 = af_masterLink + line.split("\"")[1]
                            break

                    elif test_type == TestType.EXTERNAL.value:
                        if PathExtension.EXTERNAL_DOWNLOAD_NAME_LOG.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                        .replace(ReleaseInfo.COMPILER.value, compiler.lower()) in line:
                            m_downloadLink1 = af_masterLink + line.split("\"")[1]
                            break

                    elif test_type == TestType.INTERNAL.value:
                        if PathExtension.INTERNAL_DOWNLOAD_NAME_LOG.value\
                        .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                        .replace(ReleaseInfo.COMPILER.value, compiler.lower()) in line:
                            m_downloadLink1 = af_masterLink + line.split("\"")[1]
                break

            except:
                print("Connection was refused by the server..")
                print("Let me sleep for 10 seconds")
                print("ZZzzzz...")
                time.sleep(10)
                print("Was a nice sleep, now let me continue...")
                af_pageSouce = ''
                continue

        current_dir = os.path.abspath(os.path.dirname(__file__))

        # Create file name and folder name for download file test suite that don't know error reason
        if test_type == TestType.WIRING.value:
            file_html_xml_download_name = PathExtension.\
            WIRING_DOWNLOAD_HTML_XML.value.\
            replace(ReleaseInfo.MODULE_NAME.value, module_name.lower()) + ".zip"

            file_log_download_name = PathExtension.\
            REASON_WIRING_FILE_NAME.value.\
            replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())+ ".zip"

            download_folder_extension = PathExtension.\
            REASON_WIRING_FOLDER_EXTENSION.value.\
            replace(ReleaseInfo.RELEASE.value, release_name).\
            replace(ReleaseInfo.DERIVATIVE.value, derivative).\
            replace(ReleaseInfo.MODULE_NAME.value, module_name).\
            replace(ReleaseInfo.TEST_TYPE.value, test_type)

            download_folder  = os.path.join(current_dir, \
                download_folder_extension)
            download_file_path_log = os.path.join(download_folder, \
                file_log_download_name)
            download_file_path_html_xml = os.path.join(download_folder, \
                file_html_xml_download_name)

        elif test_type == TestType.EXTERNAL.value \
        or test_type == TestType.INTERNAL.value:
            if test_type == TestType.INTERNAL.value:
                file_log_download_name = PathExtension\
                .REASON_DETAIL_INT_FILE_NAME.value\
                .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                .replace(ReleaseInfo.COMPILER.value, compiler.lower()) + ".zip"

            else:
                file_log_download_name = PathExtension\
                .REASON_DETAIL_EXT_FILE_NAME.value\
                .replace(ReleaseInfo.MODULE_NAME.value, module_name.lower())\
                .replace(ReleaseInfo.COMPILER.value, compiler.lower()) + ".zip"
            download_folder_extension = PathExtension\
            .REASON_DETAIL_FOLDER_EXTENSION.value\
            .replace(ReleaseInfo.RELEASE.value, release_name)\
            .replace(ReleaseInfo.DERIVATIVE.value, derivative)\
            .replace(ReleaseInfo.MODULE_NAME.value, module_name)\
            .replace(ReleaseInfo.COMPILER.value, compiler)\
            .replace(ReleaseInfo.TEST_TYPE.value, test_type)
            
            download_folder  = os.path.join(current_dir, \
                download_folder_extension)
            download_file_path_log = os.path.join(download_folder, \
                file_log_download_name)

        # Clear all file and folder in containing folder if exists
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        else:
            for the_file in os.listdir(download_folder):
                file_path = os.path.join(download_folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as error_log:
                    print error_log

        # Download and extract all file to containing folder
        if test_type == TestType.WIRING.value:
            # Open our local file for writing
            while 1:
                # Setting timeout for while loop is 60s
                timeout = time.time() + 60

                # Download html report for wiring test if download link exists
                if m_downloadLink2:
                    m_getdata1 = urlopen(m_downloadLink2)
                    # sys.stdout.write("Download %s ..." % (file_html_xml_download_name))
                    with open(download_file_path_html_xml, "wb") as local_file_2:
                        local_file_2.write(m_getdata1.read())
                    # sys.stdout.write("Complete!\n")
                    zip_file_html_xml = zipfile.ZipFile(download_file_path_html_xml, 'r')
                    ret_html_xml = zip_file_html_xml.testzip()
                    if ret_html_xml is not None:
                        continue
                    else:
                        zip_file_html_xml.extractall(download_folder)
                        zip_file_html_xml.close()

                # Download run and build log for wiring test
                if m_downloadLink1:
                    m_getdata = urlopen(m_downloadLink1)
                    # sys.stdout.write("Download %s ..." % (file_log_download_name))
                    with open(download_file_path_log, "wb") as local_file_1:
                        local_file_1.write(m_getdata.read())
                    # sys.stdout.write("Complete!\n")

                    zip_file_log = zipfile.ZipFile(download_file_path_log)
                    ret_log = zip_file_log.testzip()
                    if ret_log is None:
                        zip_file_log.extractall(download_folder)
                        zip_file_log.close()
                        break
                    else:
                        if os.path.isfile(os.path.join(download_folder, \
                            file_log_download_name)):
                            os.unlink(os.path.join(download_folder, \
                                file_log_download_name))

                if time.time() > timeout:
                    sys.stdout.write("Can not down load file!\n")
                    break

        else:
            while 1:
                # Setting timeout for while loop is 60s
                timeout = time.time() + 60

                # Download run and build log for other test case if download link exists
                if m_downloadLink1:
                    m_getdata = urlopen(m_downloadLink1)
                    with open(download_file_path_log, "wb") as local_file_1:
                        local_file_1.write(m_getdata.read())
                    # sys.stdout.write("Complete!\n")

                    zip_file = zipfile.ZipFile(os.path.join(download_folder, \
                        file_log_download_name))
                    ret = zip_file.testzip()
                    if ret is None:
                        zip_file.extractall(download_folder)
                        zip_file.close()
                        break
                    else:
                        if os.path.isfile(os.path.join(download_folder, \
                            file_log_download_name)):
                            os.unlink(os.path.join(download_folder, \
                                file_log_download_name))

                if time.time() > timeout:
                    break

        # Check wiring reason for module if test_type is wiring test
        if test_type == TestType.WIRING.value:
            wiring_report_file_name = list_test_suite[0] + '.html'
            wiring_report_file_path = os.path.join(download_folder, \
                wiring_report_file_name)
            f_list_reason_fail[list_test_suite[0]] = ''

            if os.path.isfile(wiring_report_file_path):
                with open(wiring_report_file_path, 'r') as html_object:
                    if Status.SUCCESS.value in html_object.read():
                        f_list_reason_fail[list_test_suite[0]] = Status.SUCCESS.value

            if f_list_reason_fail[list_test_suite[0]] != Status.SUCCESS.value:

                wiring_run_check_file = os.path.join(download_folder, \
                    PathExtension.RUN_CHECK_FILE_PATH_EXTENSION.value.\
                    replace(ReleaseInfo.TEST_SUITE.value, list_test_suite[0]))

                if os.path.isfile(wiring_run_check_file):
                    if ErrorSign.NOT_OK.value in open(wiring_run_check_file).read():
                        f_list_reason_fail[list_test_suite[0]] = Status.DO_RUN_ERROR.value

                if f_list_reason_fail[list_test_suite[0]] != Status.DO_RUN_ERROR.value:
                    wiring_build_log_file = os.path.join(download_folder, \
                        PathExtension.BUILD_LOG_FILE_PATH_EXTENSION.value.\
                        replace(ReleaseInfo.TEST_SUITE.value, list_test_suite[0]))
                    if os.path.isfile(wiring_build_log_file):
                        if ErrorSign.ERROR.value in open(wiring_build_log_file).read():
                            f_list_reason_fail[list_test_suite[0]] = Status.BUILD_FAIL.value
                    else:
                        f_list_reason_fail[list_test_suite[0]] = Status.UNKNOWN.value
        else:
            # Check reason for other internal or external test suite
            for test_suite in list_test_suite:
                f_list_reason_fail[test_suite] = ''
                run_check_file_path = os.path.join(download_folder,\
                 PathExtension.RUN_CHECK_FILE_PATH_EXTENSION.value.\
                 replace(ReleaseInfo.TEST_SUITE.value, test_suite))

                if os.path.isfile(run_check_file_path):
                    if ErrorSign.NOT_OK.value in open(run_check_file_path).read():
                        f_list_reason_fail[test_suite] = Status.DO_RUN_ERROR.value

                if f_list_reason_fail[test_suite] != Status.DO_RUN_ERROR.value:
                    build_log_file_path = os.path.join(download_folder, \
                        PathExtension.BUILD_LOG_FILE_PATH_EXTENSION.value.\
                        replace(ReleaseInfo.TEST_SUITE.value, test_suite))

                    if os.path.isfile(build_log_file_path):
                        if ErrorSign.ERROR.value in open(build_log_file_path).read():
                            f_list_reason_fail[test_suite] = Status.BUILD_FAIL.value
                    else:
                        f_list_reason_fail[test_suite] = Status.UNKNOWN.value

        return f_list_reason_fail

    ########################################################################################
    # Description : AF_GetOtherFailReason is a function that get orther failed reasion of  #
    #               test suite that don't know error reason                                #
    # Parameter   :                                                                        #
    # release_name is release information                                                  #
    # derivative is the derivative infomation                                              #
    # file is the html summary report file path                                            #
    # module_name is name of the module                                                    #
    # module_report_info is dictionary to get output of this function                      #
    # Output :                                                                             #
    # Dictionary contains all fail reason of the module                                    #
    ########################################################################################
    def AF_GetDetailReportInfo(self, release_name, derivative, 
                            file, module_name, module_report_info):
        list_test_suite = self.AF_GetListTestSuite(derivative, module_name)
        list_test_suite_fail = []
        list_test_suite_pass = []
        list_test_external_fail = []
        list_test_internal_fail = []
        list_test_suite_unkown_reason = {}
        module_report_info[TestType.INTERNAL.value] = {}
        module_report_info[TestType.EXTERNAL.value] = {}

        with open(file, 'r') as html_object:
            raw_html = BeautifulSoup(html_object, 'html.parser')

        list_table = raw_html.find_all("table")

        found_table = False
        if list_table:
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

                # remove the first row header to calculate number of test_id
                table_row = get_table_data.find_all('tr')[1:]

                for row in table_row:
                    column = row.find_all('td')
                    for index in range(len(column)):
                        
                        if ((ErrorSign.FAIL.value in column[index].contents) \
                            or (ErrorSign.NA.value in column[index].contents)) \
                        and (column[2].contents not in list_test_suite_fail):
                            list_test_suite_fail.append(column[2].contents)

                        elif (column[2].contents in list_test_suite_pass) \
                        and (column[2].contents in list_test_suite_fail):
                            list_test_suite_pass.remove(column[2].contents)

                        elif (column[2].contents not in list_test_suite_fail) \
                        and (column[2].contents not in list_test_suite_pass):
                            list_test_suite_pass.append(column[2].contents)

        # Convert test suite fail name from html file
        list_test_suite_fail_convert = self.ConvertTestSuiteName(list_test_suite_fail)

        # Convert test suite pass name from html file
        list_test_suite_pass_convert = self.ConvertTestSuiteName(list_test_suite_pass)

        # Get reason fail for test case in html file
        for compiler in self.list_compiler_short_name:
            module_report_info[TestType.INTERNAL.value][compiler] = {}
            module_report_info[TestType.EXTERNAL.value][compiler] = {}

            for test_suite_fail in list_test_suite_fail_convert: 
                if test_suite_fail in list_test_suite[TestType.EXTERNAL.value]:
                    module_report_info[TestType.EXTERNAL.value][compiler][test_suite_fail] = {}
                    list_TC_reason = self.AF_GetFailReasonFromTSHtml(derivative, \
                        compiler, test_suite_fail)
                    if list_TC_reason:
                        for k, v in list_TC_reason.iteritems():               
                            module_report_info[TestType.EXTERNAL.value][compiler][test_suite_fail][k] = v
                
                elif test_suite_fail in list_test_suite[TestType.INTERNAL.value]:
                    module_report_info[TestType.INTERNAL.value][compiler][test_suite_fail] = {}  
                    list_TC_reason = self.AF_GetFailReasonFromTSHtml(derivative, \
                        compiler, test_suite_fail)
                    if list_TC_reason:
                        for k, v in list_TC_reason.iteritems():               
                            module_report_info[TestType.INTERNAL.value][compiler][test_suite_fail][k] = v

        # Get the left test_suite that can not determine reason
        if list_test_suite[TestType.WIRING.value]:
            list_test_suite_unkown_reason[TestType.WIRING.value] = \
            list_test_suite[TestType.WIRING.value]
            list_reason_unkown = self.AF_GetOtherFailReason(release_name, \
                derivative, module_name, TestType.WIRING.value, \
                'ghs', list_test_suite_unkown_reason[TestType.WIRING.value])
            if list_reason_unkown[list_test_suite[TestType.WIRING.value][0]] != Status.SUCCESS.value:
                module_report_info[TestType.WIRING.value] = {}
                module_report_info[TestType.WIRING.value][list_test_suite[TestType.WIRING.value][0]] = \
                list_reason_unkown[list_test_suite[TestType.WIRING.value][0]]

        for test_suite_int in list_test_suite[TestType.INTERNAL.value]:
            if test_suite_int not in \
            list_test_suite_fail_convert and \
            test_suite_int not in \
            list_test_suite_pass_convert:
                list_test_internal_fail.append(test_suite_int)

        for test_suite_ext in list_test_suite[TestType.EXTERNAL.value]:
            if test_suite_ext not in \
            list_test_suite_fail_convert and \
            test_suite_ext not in \
            list_test_suite_pass_convert:
                list_test_external_fail.append(test_suite_ext)

        list_test_suite_unkown_reason[TestType.EXTERNAL.value] = list_test_external_fail
        list_test_suite_unkown_reason[TestType.INTERNAL.value] = list_test_internal_fail

        for compiler in self.list_compiler_short_name:

            if list_test_suite_unkown_reason[TestType.INTERNAL.value]:
                internal_fail_reason = self.AF_GetOtherFailReason(release_name, \
                    derivative, module_name, TestType.INTERNAL.value, \
                    compiler, list_test_suite_unkown_reason[TestType.INTERNAL.value])
                for testsuite, reason in internal_fail_reason.iteritems():
                    module_report_info[TestType.INTERNAL.value][compiler][testsuite] = reason

            # Get reason fail for external test case if it exists
            if list_test_suite_unkown_reason[TestType.EXTERNAL.value]:
                external_fail_reason = self.AF_GetOtherFailReason(release_name, \
                    derivative, module_name, TestType.EXTERNAL.value, \
                    compiler, list_test_suite_unkown_reason[TestType.EXTERNAL.value])
                for testsuite, reason in external_fail_reason.iteritems():
                    module_report_info[TestType.INTERNAL.value][compiler][testsuite] = reason

        return module_report_info

    ########################################################################################
    # Description : ConvertTestSuiteName is a function that convert test suite name getting#
    #               from html summary report file                                          #
    # Parameter   :                                                                        #
    # list_test_suite_name is a list contain all test suite to convert                     #
    # Output :                                                                             #
    # List contains converted test suite name                                              #
    ########################################################################################
    def ConvertTestSuiteName(self, list_test_suite_name):
        list_test_suite_name_convert = []
        for test_suite in list_test_suite_name:
            list_temp = test_suite[0].split("_")
            list_member_in_test_suite = []
            for item in list_temp:
                if item == 'ts':
                    list_member_in_test_suite.append(item.upper())
                elif len(list_temp) > 3:
                    if list_temp.index(item) == 1:
                        item = item.lower()
                    else:
                        item = item[0].upper() + item[1:]
                    list_member_in_test_suite.append(item)
                else:
                    item = item[0].upper() + item[1:]
                    list_member_in_test_suite.append(item)

            test_suite_name_convert = "_".join(list_member_in_test_suite)
            list_test_suite_name_convert.append(test_suite_name_convert)

        return list_test_suite_name_convert

    ########################################################################################
    # Description : GenJsonFile is a function to generate all report to json file          #
    # Parameter   :                                                                        #
    # file_path is the path of generating file                                             #
    # input_dict is data for parsing to json file                                          #
    # Output :                                                                             #
    # Json file that contain all error reason                                              #
    ########################################################################################
    def GenJsonFile(self, file_path, input_dict):
        with open(file_path, 'w') as file:
            json.dump(input_dict, file, sort_keys=True, indent=4)

    ########################################################################################
    # Description : AF_GenAllModuleReportToJson is a function to generate report of        #
    #               each module in realease to json file                                   #
    # Parameter   :                                                                        #
    # release_name is release information                                                  #
    # module_name is name of the module                                                    #
    # Output :                                                                             #
    # Json file that contain all error reason                                              #
    ########################################################################################
    def AF_GenAllModuleReportToJson(self, release_name, module_name):
        report_dir          = self.download_folder_name
        list_error_log      = []

        # Determine summary report file path
        summary_report_dir  = report_dir.replace(ReleaseInfo.REPORT_NAME.value, \
            self.summary_report_folder)
        module_info = dict([(key, {}) for key in self.list_derivative])

        # Get all fail reason of module in release
        for derivative in self.list_derivative:
            report_html_file = os.path.join(summary_report_dir.\
                replace(ReleaseInfo.DERIVATIVE.value, derivative), \
                self.template_summary_name.\
                replace(ReleaseInfo.DERIVATIVE.value, derivative).\
                replace(ReleaseInfo.MODULE_NAME.value, module_name.upper()))
            if os.path.exists(report_html_file):
                module_info[derivative]= self.AF_GetDetailReportInfo(release_name, \
                    derivative, report_html_file, \
                    module_name, module_info[derivative])
            else:
                list_error_log.append(report_html_file)

        if self.date_time_download == 0:
            self.date_time_download = self.GetCurrentDateTime()

        if not os.path.exists(self.current_report_json \
            + self.date_time_download):
            os.makedirs(self.current_report_json \
                + self.date_time_download)

        json_path = self.current_report_json \
        + self.date_time_download \
        + "\\" + module_name.upper() \
        + ".json"

        self.GenJsonFile(json_path, module_info)

        sys.stdout.write("Generate completely report of %s to json file!\n" % (module_name))

        return list_error_log