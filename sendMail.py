import socket
import base64

import os
import mimetypes
import json
import threading
import time

from datetime import *
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

max_attachment_size = 3 * 1024 * 1024  # Giới hạn kích thước là 3 MB


# Đọc cấu hình từ file config
with open('config.json', 'r') as file:
    config = json.load(file)

SMTP_SERVER = config["SMTP"]["server"]
SMTP_PORT = config['SMTP']['port']
POP3_SERVER = config['POP3']['server']
POP3_PORT = config['POP3']['port']
USERNAME = config['Account']['username']
PASSWORD = config['Account']['password']


# Dia chi server
ADDR = (SMTP_SERVER, SMTP_PORT)
FORMAT = 'utf-8'


def listOfRecepients():
    LIST = []
    s = input('List of recepients:')
    for i in s.split():
        LIST.append(i)
    else:
        for i in LIST:
            print(i)

    return LIST


def chooseMode():
    list_to = []
    list_cc = []
    list_bcc = []

    to = int(input('TO:'))
    if to == 1:
        list_to = listOfRecepients()

    cc = int(input('Cc:'))
    if cc == 1:
        list_cc = listOfRecepients()

    bcc = int(input('Bcc: '))
    if bcc == 1:
        list_bcc = listOfRecepients()

    return list_to, list_cc, list_bcc


def writeBodyText():
    subject = input('Subject: ')
    content = input('Write text body: ')
    attachment_check = False
    s = int(input('Do you want to send with attachment files: '))
    if s == 1:
        attachment_check = True
    return subject, content, attachment_check


def rcpToCommand(client, list_recepient):
    for i in list_recepient:
        rcpt_to_command = f'RCPT TO: <{i}>\r\n'
        client.sendall(rcpt_to_command.encode(FORMAT))
        rcpt_to_response = client.recv(1024).decode(FORMAT)
        print(rcpt_to_response)


def converToListForPrint(list_recepient):
    if len(list_recepient) == 1:
        header = f'{list_recepient[0]}'
    else:
        header = ','.join(list_recepient[:-1])
        header += f', {list_recepient[-1]}' if list_recepient else ''
    return header


def checkAttachFile():
    sum_attachment_size = 0
    list_file_path = []
    while True:
        file_path = input('Nhap duong dan (nhap \'quit\' de ket thuc): ')
        if file_path.lower() == 'quit':
            break
        file_path_exist = os.path.exists(file_path)
        if not file_path_exist:
            print('Duong dan khong ton tai.')

        size = os.path.getsize(file_path)
        sum_attachment_size += size
        if sum_attachment_size <= max_attachment_size:
            list_file_path.append(file_path)
        else:
            print("Kích thước tệp tin vượt quá giới hạn.")
            break

    return list_file_path


def sendMail(sender_email):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # ket noi voi server
        client.connect(ADDR)
        introduce_msg = client.recv(1024).decode(FORMAT)
        print(introduce_msg)

        # login(client)

        # bat dau cuoc tro chuyen
        ehlo_command = f'EHLO ' + '[' + SMTP_SERVER + ']' '\r\n'
        client.sendall(ehlo_command.encode(FORMAT))
        ehlo_respond = client.recv(1024).decode(FORMAT)
        print(ehlo_respond)

        # bat dau chuyen thu
        mail_from_command = f'MAIL FROM: <{sender_email}>\r\n'
        client.sendall(mail_from_command.encode(FORMAT))
        mail_from_response = client.recv(1024).decode(FORMAT)
        print(mail_from_response)

        # chi dinh nguoi nhan bang list duoc dua vao
        list_to, list_cc, list_bcc = chooseMode()
        if len(list_to) != 0:
            rcpToCommand(client, list_to)
            header_to = converToListForPrint(list_to)
        if len(list_cc) != 0:
            rcpToCommand(client, list_cc)
            header_cc = converToListForPrint(list_cc)
        if len(list_bcc) != 0:
            rcpToCommand(client, list_bcc)
            header_bcc = 'undisclosed-recipients: ;'

        subject, content, attachment_check = writeBodyText()

        # tao noi dung gui
        data_command = 'DATA\r\n'
        client.sendall(data_command.encode(FORMAT))
        # data_response = client.recv(1024).decode(FORMAT)
        # print(data_response)

        current_datetime = datetime.now()
        msg = MIMEMultipart()
        msg['Date'] = f'{current_datetime.strftime(
            "%a , %Y-%m-%d %H:%M:%S")}\r\n'
        msg['From'] = f'{sender_email}'
        msg['Subject'] = f'{subject}'
        if len(list_to) != 0:
            msg['To'] = header_to
        if len(list_cc) != 0:
            msg['Cc'] = header_cc
        if len(list_bcc) != 0:
            msg['To'] = header_bcc

        body = MIMEText(content, 'plain')
        msg.attach(body)

        if attachment_check:
            list_file_path = checkAttachFile()
            for file_path in list_file_path:
                filename = os.path.basename(file_path)
                file_mime_type, _ = mimetypes.guess_type(file_path)

                if file_mime_type:
                    part = MIMEBase(*file_mime_type.split('/'))
                    print(part)

                    with open(file_path, 'rb') as file:
                        part.set_payload(file.read())

                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename="{filename}"')

                    msg.attach(part)
        # gui thu
        client.sendall(msg.as_bytes() + b'\r\n.\r\n')

    finally:
        # Kết thúc kết nối
        quit_command = f'QUIT\r\n'
        client.sendall(quit_command.encode(FORMAT))

        client.close()
