from email.mime.text import MIMEText
import smtplib


default_mail_addr = 'noreply.zuricapltd@gmail.com'
default_pwd = 'noreply2017'
allowed_addr = {default_mail_addr: default_pwd}


def send_mail(mail_to, message, subject, mail_from=None):
    if mail_from is None:
        mail_from = default_mail_addr
        pwd = allowed_addr[default_mail_addr]
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(mail_from, pwd)
        server.send_message(mail_from, mail_to, msg.as_string())
        server.quit()
    except Exception as e:
        raise Exception(e)
