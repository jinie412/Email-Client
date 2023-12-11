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
            "%a, %Y-%m-%d %H:%M:%S")}\r\n'
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


DOWNLOAD_PATH = 'downloaded'
SPAM_FOLDER = 'spam'
INBOX_FOLDER = 'inbox'
STUDY_FOLDER = 'study'
PERSONAL_FOLDER = 'personal'
PROJECT_FOLDER = 'project'

FILTER_RULES = {
    'Project': ['ahihi@testing.com', 'ahuu@testing.com'],
    'Important': ['urgent', 'ASAP'],
    'Work': ['report', 'meeting'],
}

# Từ khóa spam
SPAM_KEYWORDS = ['virus', 'hack', 'crack']

# Tạo thư mục để lưu trữ email tải về và thư mục Spam
# if not os.path.exists(DOWNLOAD_PATH):
#     os.makedirs(DOWNLOAD_PATH)
# if not os.path.exists(SPAM_FOLDER):
#     os.makedirs(INBOX_FOLDER)
# if not os.path.exists(SPAM_FOLDER):
#     os.makedirs(STUDY_FOLDER)
# if not os.path.exists(PERSONAL_FOLDER):
#     os.makedirs(PERSONAL_FOLDER)
# if not os.path.exists(PROJECT_FOLDER):
#     os.makedirs(PROJECT_FOLDER)


def download_email(uid, client_socket):
    # Gửi lệnh để tải nội dung email theo UID
    client_socket.sendall(f'RETR {uid}\r\n'.encode())

    # Nhận phản hồi từ server
    response = client_socket.recv(1024).decode()
    print(response)

    # Đọc dữ liệu từ server và lưu vào tệp
    email_content = b''
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        email_content += data

    # Lưu nội dung email vào tệp
    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    with open(file_path, 'wb') as email_file:
        email_file.write(email_content)

    return file_path


def move_to_spam(uid, client_socket):
    client_socket.sendall(f'DELE {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    spam_file_path = os.path.join(SPAM_FOLDER, f'spam_email.{uid}.txt')

    with open(file_path, 'r', encoding='utf-8') as original_email:
        email_content = original_email.read()
    with open(spam_file_path, 'w', encoding='utf-8') as spam_email:
        spam_email.write(email_content)

    os.remove(file_path)
    print(f"Email voi UID {uid} da duoc chuyen toi thu muc Spam.")


def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list


def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))


def move_to_folder(uid, client_socket, folder):
    client_socket.sendall(f'DELE {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
    folder_file_path = os.path.join(
        folder, f'{folder.lower()}_email_{uid}.txt')

    with open(file_path, 'r', encoding='utf-8') as original_email:
        email_content = original_email.read()

    with open(folder_file_path, 'w', encoding='utf-8') as folder_email:
        folder_email.write(email_content)

    os.remove(file_path)

    print(f"Email with UID {uid} is moved to {folder} folder.")


def apply_filters(uid, email_content, client_socket):
    for folder, keywords in FILTER_RULES.items():
        if any(keyword.lower() in email_content.lower() for keyword in keywords):
            move_to_folder(uid, client_socket, folder)

    if any(keyword.lower() in email_content.lower() for keyword in SPAM_KEYWORDS):
        move_to_folder(uid, client_socket, SPAM_FOLDER)


def parse_email_content(email_content):
    list_sender = []
    subject = None
    content = None
    start_line = None
    end_line = None
    count = 0

    lines = email_content.split("\r\n")
    print(lines)
    for line in lines:
        # Tìm thông tin sender
        if line.startswith("From: "):
            sender = line[6:].strip()
            print(sender)
            list_sender.append(sender)

        # Tìm thông tin subject
        elif line.startswith("Subject: "):
            subject = line[9:].strip()
            print(subject)

        # Bắt đầu đọc nội dung
        elif line == "Content-Transfer-Encoding: 7bit":
            start_line = line

        elif line.startswith("--==============="):
            end_line = line
            count += 1
            if count == 2:
                start_index = lines.index(start_line)
                end_index = lines.index(end_line)
                content = lines[start_index+1:end_index]
                print(content)
                break

    return {"sender": list_sender, "subject": subject, "content": content}


def classify_email(email, FilterRules):
    for rule in FilterRules:
        if rule['type'] == 'sender' and email.sender == rule['value']:
            return rule['folder']
        elif rule['type'] == 'subject' and rule['value'] in email.subject:
            return rule['folder']
        elif rule['type'] == 'keyword' and rule['value'] in email.content:
            return rule['folder']
    return 'Inbox'  # Mặc định nếu không phù hợp


def filter_mail(list_mail):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    for mail in list_mail:
        email = parse_email_content(mail[1])
        folder = classify_email(email, config['FilterRules'])


# in ra list cac noi dung mail
def mail_content(client, numberOfmsg):
    list_mail_content = []
    for i in range(1, numberOfmsg+1):
        client.sendall(f'RETR {i}\r\n'.encode())
        response_retr = client.recv(1024).decode()
        list_mail_content.append(response_retr)

    return list_mail_content

# in ra list cac id mail


def id_mail(uid_list_response):
    list_id_mail = []
    for i in uid_list_response:
        _, id = i.split()
        list_id_mail.append(id)
    return list_id_mail

# in ra list gom tung cap id mail va noi dung mail tuong ung


def full_mail(list_id_mail, list_mail_content):
    list_mail = []
    for i, j in zip(list_id_mail, list_mail_content):
        d = (i, j)
        list_mail.append(d)

    return list_mail


def store_mail_to_txt(full_mail):
    # dat ten id_mail cho file text
    f = open(f'{full_mail[1]}.txt', 'x')


def receiveEmail():
    base = 1024

    # Kết nối đến Mail Server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((POP3_SERVER, POP3_PORT))

    # Nhận phản hồi từ server khi kết nối
    response = client_socket.recv(1024).decode()
    print(response)

    # Xác thực đăng nhập
    client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(b'STAT\r\n')
    response_stat = client_socket.recv(base).decode()
    print(response_stat)

    client_socket.sendall(b'LIST\r\n')
    response_list = client_socket.recv(base).decode()
    print(response_list)

    client_socket.sendall(b'UIDL\r\n')
    response_uid = client_socket.recv(1024).decode()
    print(response_uid)
    uid_list_response = response_uid.splitlines()[1:]

    # xoa dau cham cuoi cung trong list
    uid_list_response.remove('.')
    print(uid_list_response)

    # tach cac so thu tu de lay id mail
    list_id_mail = id_mail(uid_list_response)

    numberOfmsg = len(uid_list_response)

    # lay phan body mail voi tung so thu tu voi lenh RETR
    list_mail_content = mail_content(client_socket, numberOfmsg)
    parse_email_content(list_mail_content[2])

    # tao list cac tuple de luu id mail va body mail tuong ung
    list_mail = full_mail(list_id_mail, list_mail_content)

    client_socket.sendall(b'QUIT\r\n')
    # response_quit = client_socket.recv(1024).decode()
    # print(response_quit)

    client_socket.close()


# Thư mục để lưu email tải về
INBOX_FOLDER = 'Spam'


def retrieve_email(pop3_socket, email_id):
    pop3_socket.sendall(f"RETR {email_id}\r\n".encode())
    email_content = pop3_socket.recv(4096).decode()

    # Lưu nội dung email vào file trong thư mục Inbox
    email_filename = os.path.join(INBOX_FOLDER, f"email_{email_id}.txt")
    with open(email_filename, 'w') as email_file:
        email_file.write(email_content)


def receiveMail():
    # Tạo thư mục Inbox nếu chưa tồn tại
    os.makedirs(INBOX_FOLDER, exist_ok=True)

    while True:
        # Kết nối với máy chủ POP3
        pop3_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pop3_socket.connect((POP3_SERVER, POP3_PORT))

        receive_data = pop3_socket.recv(1024).decode()
        print(receive_data)

        user_command = f"USER {USERNAME}\r\n"
        pop3_socket.sendall(user_command.encode())
        receive_data = pop3_socket.recv(1024).decode()
        print(receive_data)

        pass_command = f"PASS {PASSWORD}\r\n"
        pop3_socket.sendall(pass_command.encode())
        receive_data = pop3_socket.recv(1024).decode()
        print(receive_data)

        # Nhận danh sách thư
        pop3_socket.sendall(b"LIST\r\n")
        receive_data = pop3_socket.recv(1024).decode()
        print(receive_data)

        # Lấy danh sách thư
        email_list = []
        while True:
            pop3_socket.sendall(b"RETR\r\n")
            receive_data = pop3_socket.recv(1024).decode()
            if receive_data.startswith("+OK"):
                email_list.append(receive_data)
            else:
                break

        # Tải và lưu email
        for email_id in range(1, len(email_list) + 1):
            retrieve_email(pop3_socket, email_id)

        pop3_socket.sendall(b"QUIT\r\n")
        receive_data = pop3_socket.recv(1024).decode()
        print(receive_data)

        break


if __name__ == "__main__":
    # sendMail('seokjin@gmail.com')
    receiveEmail()
