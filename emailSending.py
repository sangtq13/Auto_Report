'''
Created on 24-Jan-2018
'''

import smtplib as m
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import config
import os
import socks
from configManagmentInterface import ConfigManagmentInterface

#socks.setdefaultproxy(TYPE, ADDR, PORT)
# socks.setdefaultproxy(socks.HTTP, 'fsoft-proxy.fsoft.fpt.vn', 8080)
# socks.wrapmodule(m)

class EmailSending(ConfigManagmentInterface):
    """docstring for EmailSending
        Contain routine to create and send email 
    """
    #server to connect to 
    SERVER = "smtp.office365.com"
    #port for the connection to the server
    PORT = 587
    def __init__(self,p_release_name):
        """ Create the object email, including a object SMTP
        """
        super(EmailSending, self).__init__(p_release_name)
        try:
            self.smtp = m.SMTP(self.SERVER, self.PORT)
            pass
        except Exception as e:
            raise e
            print "Cannot init smtp sever with %s",e
        else:
            print "Init done!!!"
            pass
        self.smtp.ehlo()
        self.smtp.starttls()    
        self.smtp.login(self.email_operator, self.pass_word_operator)
        print "Logging done!!!"

    def exit(self):
        """ Close the SMTP connection 
        """
        self.smtp.quit()
        print "Close the connection!!!"

    def send(self, from_addr, to_addr, text):
        """send email 
        :param from_addr: address of the sender
        :param to_address: list containing all the addresses of the receiver (include cc)
        :param text: mail into a string
        """
        return self.smtp.sendmail(from_addr, to_addr, text)
    def generate_email_string(self,from_addr, to_addr, body, cc=None, subject=None, attachement_xlsx=None):
        """generate the email based on the info given

        :param from_addr: email address of the sender
        :param to_addr: email address of the destination
        :param body: text for the body of the email
        :param subject: subject of the email
        :param attachement_xlsx: path to the attachement file (only xlsx file)
        :return complete email in a string format
        """
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject
        if cc is not None:
            msg['cc'] = ", ".join(cc)
        msg.attach(MIMEText(body, 'plain'))
        if attachement_xlsx is not None:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(attachement_xlsx, "rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.split(attachement_xlsx)[1]))
            msg.attach(part)

        text = msg.as_string()
        return text
    def genertate_body_email(self, receiver):
        message_text = "In the attached file, you can find the general status of your module! \r\n\r\nThanks and Best Regards \r\nNXP_SDK Automation Team" 
        body_text_1  = "Hello "
        body_text_1 += receiver
        body_text_1 += "\r\n\r\n"
        body_text_1 +=message_text   
        return body_text_1
        pass
    def run(self):
        print "Start to sending email!!!"
        for key in self.email_list:
            body_text  = self.genertate_body_email(key)
            attachement_file = self.release_name + "_Test_Status_Reports.xlsx"
            subject ="[" +self.release_name+"]"+"[Report from ATE]"
            if os.path.exists(attachement_file):
                email_text = self.generate_email_string(self.email_operator, self.email_list[key], body_text, \
                                                        subject=subject, \
                                                        cc = [self.email_operator] , \
                                                        attachement_xlsx = attachement_file)
                print ("Sending email to : {0}".format(key))
                self.send(self.email_operator, self.email_list[key], email_text)
            else :
                print "The output file doen not exit!!!"
        # Closing the connection 
        self.exit()
if __name__ == '__main__':
    objEx = EmailSending()
    objEx.run()