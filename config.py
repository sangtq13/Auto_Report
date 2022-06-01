'''
Created on 17-Jan-2018
'''


# ----- Account access infomation ----
USR_Name = 'S13'                     # Eg:   S13
Email = 's13@example.com'                      # Eg:   s13@example.com
USR = 'nxf42998'                                # Eg:   nxf42998
PWD = '123456'                                        # Eg:   '************'
#list containing CC email address and name ([name, email_address]) for all the email send. leave empty if not needed
CC = [USR_Name, Email]
# ---- Input jira server link
JIRA_Link = 'https://jira.sw.nxp.com'           # Eg:   'https://jira.sw.nxp.com'
# ---- Input command filter
CMD_Filter = ''
# ---- The link to jira your filter by this command ----
JIRA_Filter_Link = ''   
# HEADLine detail for excel file
HEADLine    =  ['Issue Type', 'Key', 'Summary', 'Assignee', 'Reporter', 'Priority', 'Status',
                'Resolution', 'Created', 'Resolved', 'Linked Issues', 'Due Date', 'Tester Assigned',
                'Fix Version/s', 'Resolved Build ID', 'Test Report', 'Labels', 'Board(s) Affected',
                'Device', 'Resolution Text', 'Root Cause (cascading)', 'Severity' ]
SIZE        =  []
# Declare name for excel generate file
EXCEL_GENERATE_NAME  = ''
#name of the excel file containing the the data about the testers
PROJECT_DATA_FILE = ""

# EOF
