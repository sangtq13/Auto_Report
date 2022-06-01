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
from configManagmentInterface import ConfigManagmentInterface

import color_table
reload(sys)
sys.setdefaultencoding('utf8')

class DownloadTestFromATE(ConfigManagmentInterface):
    """docstring for DownloadTestFromATE
        Input :
            Name of derivatives and the webpages 
            Eg: http://coral.ea.freescale.net/0/project/fileexplorer/RTpcbG9jYWxfMDNcb3V0cHV0XGxvZ3M= (K148)
        Output: 
        -Download the test results from ATE
            + Tm files ( text format)
            + Tesummary Reports (html format)
            Note: All files downloaded from ATE stored at /current_dir/[Release_Name]/[Derivatives]
    """
    def __init__(self,p_release_name):
        super(DownloadTestFromATE, self).__init__(p_release_name)

    def DownloadReport(self):
        self.date_time_download = self.GetCurrentDateTime()
        af_image_download_name  = "package16.png"
        self.list_download_derivative.sort()
        self.list_download_report.sort()
        for derivetive in self.list_download_derivative:
            print "Time start: ", self.GetCurrentDateTime()
            af_download_link    = self.derivative_info[derivetive]
            af_masterLink       = "/".join(af_download_link.split("/")[0:3])

            # get page source
            af_pageSouce = requests.get(af_download_link).text.encode('utf8')
            af_listPageSourceLine = af_pageSouce.split("\n")
            af_NumberLine = len(af_listPageSourceLine)

            # get report link, start searching link from page source, folder link is sorted => search will more quickly
            af_listReportLink = []
            af_lineStart = 0
            for report_type in self.list_download_report:
                for line in range(af_lineStart, af_NumberLine):
                    if self.ate_info[report_type] in af_listPageSourceLine[line]:
                        af_listReportLink.append(af_masterLink + \
                            af_listPageSourceLine[line].split("\"")[1])
                        af_lineStart = line
                        break

            # Get link and download for each report
            for count in range(len(self.list_download_report)):
                m_reportPageSource = (requests.get(af_listReportLink[count]).\
                    text.encode('utf8')).split("\n")
                for line in range(len(m_reportPageSource)):
                    if af_image_download_name in m_reportPageSource[line]:
                        m_downloadLink = af_masterLink + \
                        m_reportPageSource[line].split("\"")[3]

                        m_getData        = requests.get(m_downloadLink, stream=True)
                        fileDownloadName = derivetive + "_" + \
                        self.list_download_report[count] + \
                        ".tar.gz"
                        download_folder  = self.download_folder_name.\
                        replace("DERIVATIVE", derivetive).\
                        replace("REPORT_NAME", self.list_download_report[count])

                        download_file_path = os.path.join(download_folder, fileDownloadName)
                        if not os.path.exists(download_folder):
                            os.makedirs(download_folder)
                        else:
                            for the_file in os.listdir(download_folder):
                                file_path = os.path.join(download_folder, the_file)
                                try:
                                    if os.path.isfile(file_path):
                                        os.unlink(file_path)
                                    elif os.path.isdir(file_path): shutil.rmtree(file_path)
                                except Exception as error_log:
                                    print error_log

                        sys.stdout.write("Download %s ..." % (fileDownloadName))
                        with open(download_file_path, "wb") as download_data:
                            download_data.write(m_getData.content)
                        sys.stdout.write("Complete!\n")
                        break
            print "Time end: %s \n" % (self.GetCurrentDateTime())
        pass
    def UnzipReportFile(self):
        for derivetive in self.list_download_derivative:
            for report_type in self.list_download_report:
                folder  = self.download_folder_name.\
                replace("DERIVATIVE", derivetive).\
                replace("REPORT_NAME", report_type)

                sys.stdout.write("\nUnzip %s ..." % (derivetive + "_" + report_type))
                for file_name in os.listdir(folder):
                    if file_name.endswith(".tar.gz"):
                        tar = tarfile.open(os.path.join(folder, file_name), "r:gz")
                        tar.extractall(folder)
                        tar.close()

                for file_name in os.listdir(folder):
                    if (file_name.endswith(".tar")):
                        tar = tarfile.open(os.path.join(folder, file_name), "r:")
                        tar.extractall(folder)
                        tar.close()

                for file_name in os.listdir(folder):
                    if (file_name.endswith(".zip")):
                        zip_file = zipfile.ZipFile(os.path.join(folder, file_name), 'r')
                        zip_file.extractall(folder)
                        zip_file.close()
                sys.stdout.write("Done\n")

                # Rename folder that contain the html file report of each compiler 
                for path in os.listdir(folder):
                    if not os.path.isdir(os.path.join(folder, path)):
                        continue # Not a directory
                    elif path == 'armc':
                        os.rename(os.path.join(folder, path), os.path.join(folder, 'ARMC'))
                    elif path == 'gcc':
                        os.rename(os.path.join(folder, path), os.path.join(folder, 'GCC'))
                    elif path == 'GreenHills_Multi':
                        os.rename(os.path.join(folder, path), os.path.join(folder, 'GHS'))
                    elif path == 'IAR_Embedded_Workbench':
                        os.rename(os.path.join(folder, path), os.path.join(folder, 'IAR'))
                    elif path == 'Windriver_DIAB':
                        os.rename(os.path.join(folder, path), os.path.join(folder, 'DIAB'))

        pass
    def run(self):
        self.DownloadReport()
        self.UnzipReportFile()
        pass