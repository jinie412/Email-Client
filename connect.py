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

        sum_attachment_size += os.path.getsize(file_path)
        if sum_attachment_size <= max_attachment_size:
            list_file_path.append(file_path)
        else:
            print("Kích thước tệp tin vượt quá giới hạn.")
            break

    return list_file_path


def sendMail(sender_email):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # try:
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

                with open(file_path, 'rb') as file:
                    part.set_payload(file.read())

                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                f'attachment; filename="{filename}"')

                msg.attach(part)
    # gui thu
    client.sendall(msg.as_string().encode(FORMAT))
    client.sendall(b'\r\n.\r\n')

    # finally:
    #     # Kết thúc kết nối
    #     quit_command = f'QUIT\r\n'
    #     client.sendall(quit_command.encode(FORMAT))
    #     quit_response = client.recv(1024).decode(FORMAT)
    #     print(quit_response)
    #     client.close()


# class EmailClient:
#     # ... (các phương thức và thuộc tính khác)

#     def display_menu(self):
#         print("Vui lòng chọn Menu:")
#         print("1. Để gửi email")
#         print("2. Để xem danh sách các email đã nhận")
#         print("3. Thoát")

#     def run(self):
#         while True:
#             self.display_menu()
#             choice = input("Nhập lựa chọn của bạn: ")

#             if choice == '1':
#                 # Gọi phương thức gửi email ở đây
#                 pass
#             elif choice == '2':
#                 # Gọi phương thức xem danh sách email ở đây
#                 pass
#             elif choice == '3':
#                 print("Tạm biệt!")
#                 break
#             else:
#                 print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")

# ----------------------------------------------------------------------------
DOWNLOAD_PATH = 'downloaded_emails'
SPAM_FOLDER = 'spam_emails'


# Tạo thư mục để lưu trữ email tải về và thư mục Spam
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)
if not os.path.exists(SPAM_FOLDER):
    os.makedirs(SPAM_FOLDER)


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


# Đường dẫn đến file lưu trạng thái email
state_filename = 'email_state.json'


def auto_fetch_email(interval, email_state):
    while True:
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

        # Lấy danh sách UID
        client_socket.sendall(b'UIDL\r\n')
        response = client_socket.recv(1024).decode()
        # Bỏ qua dòng đầu tiên chứa thông tin số lượng email
        uid_list_response = response.splitlines()[1:]
        print(uid_list_response)

        # Lặp qua danh sách UID và xử lý email
        for uid_response in uid_list_response:
            uid = uid_response.split()[0]

            # Kiểm tra xem email đã được tải trước đó hay chưa
            if not os.path.exists(os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')):
                file_path = download_email(uid, client_socket)
                with open(file_path, 'r', encoding='utf-8') as email_file:
                    email_content = email_file.read()
                    if 'sender@gmail.com' in email_content:
                        move_to_spam(uid, client_socket)
                        print(f"Email voi UID {
                              uid} da duoc di chuyen toi Spam dua tren nguoi gui")
                    if 'spam' in email_content.lower():
                        move_to_spam(uid, client_socket)
                        print(f"Email voi UID {
                              uid} da duoc di chuyen toi Spam dua tren chu de(Subject)")
                    if 'spam_content' in email_content.lower():
                        move_to_spam(uid, client_socket)
                        print(f"Email voi UID {
                              uid} da duoc di chuyen toi Spam dua tren noi dung")

            # Xử lí trạng thái thư
            # for email_id in range(1, len(email_list) + 1):
            #     if email_id not in email_state:
            #         mark_as_unread(email_id, email_state)
            #     else:
            #         mark_as_read(email_id, email_state)

            client_socket.sendall(b'QUIT\r\n')
            response = client_socket.recv(1024).decode()
            print(response)

            client_socket.close()

        # Lưu trạng thái email sau mỗi lượt tải
        save_email_state(email_state)

        # Đợi khoảng thời gian trước khi tải email tiếp theo
        time.sleep(interval)


# def load_email_state():
#     if os.path.exists(state_filename):
#         with open(state_filename, 'r') as state_file:
#             return json.load(state_file)
#     else:
#         return {}

# # Hàm đánh dấu thư đã đọc


# def mark_as_read(email_id, email_state):
#     # Đánh dấu email là đã đọc
#     for i, (sender, subject, is_read) in enumerate(email_state):
#         if i + 1 == email_id:
#             email_state[i] = (sender, subject, True)
#             print(f"Email ID {email_id} marked as read.")
#             break

# # Hàm đánh dấu thư chưa đọc


# def mark_as_unread(email_id, email_state):
#     # Đánh dấu email là chưa đọc
#     for i, (sender, subject, is_read) in enumerate(email_state):
#         if i + 1 == email_id:
#             email_state[i] = (sender, subject, False)
#             print(f"Email ID {email_id} marked as unread.")
#             break

# # Hàm lưu trạng thái email vào file


# def save_email_state(email_state):
#     # Mở file để ghi
#     with open(state_filename, 'w') as state_file:
#         for email_id, (sender, subject, is_read) in enumerate(email_state, start=1):
#             # Xây dựng định dạng dòng trong file
#             line_format = "{status} {sender}, {subject}\n"
#             status = "" if is_read else "(chưa đọc)"
#             line = line_format.format(
#                 status=status, sender=sender, subject=subject)

#             # Ghi dòng vào file
#             state_file.write(line)

#     print(f"Email state saved to {state_filename}")


if __name__ == "__main__":
    sendMail('seokjin@gmail.com')
    # Đọc trạng thái email từ file
    email_state = load_email_state()

    # Bắt đầu thread tự động tải email
    # Lưu thời gian tải tự động được cài đặt trong file cấu hình
    interval = int(config['Autoload']['interval'])
    auto_fetch_thread = threading.Thread(
        target=auto_fetch_email, args=(interval, email_state))
    auto_fetch_thread.start()

    # Gửi/nhận email và xử lý trạng thái theo yêu cầu từ người dùng
    # ...

    # Chờ thread tự động tải email kết thúc khi thoát chương trình
    auto_fetch_thread.join()

    # Lưu trạng thái email khi tắt chương trình
    save_email_state(email_state)
