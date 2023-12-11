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

                    with open(file_path, 'rb') as file:
                        part.set_payload(file.read())

                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f'attachment; filename="{filename}"')

                    msg.attach(part)
        # gui thu
        client.sendall(msg.as_string().encode(FORMAT))
        client.sendall(b'\r\n.\r\n')

    finally:
        # Kết thúc kết nối
        quit_command = f'QUIT\r\n'
        client.sendall(quit_command.encode(FORMAT))
        quit_response = client.recv(1024).decode(FORMAT)
        print(quit_response)
        client.close()


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


# =============================================================
DOWNLOAD_PATH = "downloaded_emails"
PROJECT_FOLDER = 'Project'
IMPORTANT_FOLDER = 'Important'
WORK_FOLDER = 'Work'
SPAM_FOLDER = 'Spam'

# Quy tắc lọc
FILTER_RULES = {
    'Project': ['ahihi@testing.com', 'ahuu@testing.com'],
    'Important': ['urgent', 'ASAP'],
    'Work': ['report', 'meeting'],
}

# Từ khóa spam
SPAM_KEYWORDS = ['virus', 'hack', 'crack']


PASSWORD = "your_email_password"
DOWNLOAD_PATH = "downloaded_emails"


def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list


def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))


def decode_base64(data):
    return base64.b64decode(data).decode('utf-8')


def download_email(uid, client_socket):
    client_socket.sendall(f'RETR {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    email_content = ''
    while True:
        data = client_socket.recv(4096).decode()
        email_content += data
        if data.endswith('\r\n.\r\n'):
            break

    return email_content


def save_attachment(attachment_data, filename):
    with open(filename, 'wb') as attachment_file:
        attachment_file.write(base64.b64decode(attachment_data))


def process_multipart(multipart_data, uid):
    boundary = multipart_data.get_content_type().split("=")[-1]
    parts = multipart_data.get_payload()

    for part in parts:
        process_part(part, uid)


def process_part(part, uid):
    content_type = part.get_content_type()
    content_disposition = part.get("Content-Disposition")

    if content_type.startswith("text"):
        # Xử lý phần văn bản
        content = part.get_payload(decode=True).decode('utf-8')
        print(f"Text content:\n{content}")
    elif content_disposition and content_disposition.startswith("attachment"):
        # Xử lý phần đính kèm
        filename = part.get_filename()
        if filename:
            filename = f'{uid}_{filename}'
            save_attachment(part.get_payload(), filename)
            print(f"Saved attachment: {filename}")
    elif content_type.startswith("multipart"):
        # Xử lý phần multipart (đệ quy)
        process_multipart(part, uid)


def process_mime(email_content, uid):
    lines = email_content.split('\r\n')

    # Tìm dòng bắt đầu của phần MIME
    start_index = None
    for i, line in enumerate(lines):
        if line.startswith("--"):
            start_index = i
            break

    if start_index is not None:
        # Xử lý từ dòng bắt đầu của phần MIME
        mime_data = '\r\n'.join(lines[start_index:])
        msg_start = email_content.find(mime_data)
        mime_msg = email_content[msg_start:]

        # Phân tích MIME message
        message = email.message_from_string(mime_msg)

        # Xử lý từng phần trong message
        for part in message.walk():
            process_part(part, uid)
    else:
        # Nếu không tìm thấy dòng bắt đầu của phần MIME, xử lý nội dung trực tiếp
        process_part(email.message_from_string(email_content), uid)


def get_uid_list(response):
    lines = response.splitlines()[1:]
    return [uid.split()[0] for uid in lines]


def get_uid_from_response(response):
    lines = response.splitlines()
    if lines[0].startswith(b'+OK'):
        return lines[1].split()[0].decode('utf-8')
    else:
        return None


def main():
    downloaded_uids = read_uid_list()

    # Lấy danh sách UID
    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = get_uid_from_response(uid_response)
        if uid and uid not in downloaded_uids:
            email_content = download_email(uid, client_socket)

            # Xử lý MIME để trích xuất nội dung và đính kèm
            process_mime(email_content, uid)

            # Ghi nội dung email vào tệp
            file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
            with open(file_path, 'w', encoding='utf-8') as email_file:
                email_file.write(email_content)

            downloaded_uids.add(uid)

    write_uid_list(downloaded_uids)

    client_socket.sendall(b'QUIT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.close()


def apply_filters(uid, email_content, client_socket):
    for folder, keywords in FILTER_RULES.items():
        if any(keyword.lower() in email_content.lower() for keyword in keywords):
            move_to_folder(uid, client_socket, folder)

    if any(keyword.lower() in email_content.lower() for keyword in SPAM_KEYWORDS):
        move_to_folder(uid, client_socket, SPAM_FOLDER)


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
        # save_email_state(email_state)

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


def get_uid_list(client_socket):
    client_socket.sendall(b'UIDL\r\n')

    while True:
        response = client_socket.recv(4096).decode()
        if response.startswith('+OK'):
            break

    # Tiếp tục đọc dữ liệu
    uid_list_response = response.splitlines()[1:]
    return [uid.split()[0] for uid in uid_list_response]


# def process_mime(email_content, uid):
#     lines = email_content.split('\r\n')

#     # Tìm dòng bắt đầu của phần MIME
#     start_index = None
#     for i, line in enumerate(lines):
#         if line.startswith("--"):
#             start_index = i
#             break

#     if start_index is not None:
#         # Xử lý từ dòng bắt đầu của phần MIME
#         mime_data = '\r\n'.join(lines[start_index:])
#         msg_start = email_content.find(mime_data)
#         mime_msg = email_content[msg_start:]

#         # Phân tích MIME message
#         message = email.message_from_string(mime_msg)

#         # Xử lý từng phần trong message
#         for part in message.walk():
#             process_part(part, uid)
#     else:
#         # Nếu không tìm thấy dòng bắt đầu của phần MIME, xử lý nội dung trực tiếp
#         process_part(email.message_from_string(email_content), uid)

DOWNLOAD_PATH = "downloaded_emails"


def read_uid_list():
    uid_list = set()
    if os.path.exists('uid_list.txt'):
        with open('uid_list.txt', 'r') as file:
            uid_list = set(file.read().splitlines())
    return uid_list


def write_uid_list(uid_list):
    with open('uid_list.txt', 'w') as file:
        file.write('\n'.join(uid_list))


def decode_base64(data):
    return base64.b64decode(data).decode('utf-8')


def download_email(uid, client_socket):
    client_socket.sendall(f'RETR {uid}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    email_content = ''
    while True:
        data = client_socket.recv(4096).decode()
        email_content += data
        if data.endswith('\r\n.\r\n'):
            break

    return email_content


def save_attachment(attachment_data, filename):
    with open(filename, 'wb') as attachment_file:
        attachment_file.write(base64.b64decode(attachment_data))


def process_part(part, uid):
    content_type = part.split(
        b'\r\nContent-Type: ')[1].split(b'\r\n')[0].decode('utf-8')
    content_disposition = part.split(
        b'\r\nContent-Disposition: ')[1].split(b'\r\n')[0].decode('utf-8')

    if content_type.startswith("text"):
        # Xử lý phần văn bản
        content = part.split(b'\r\n\r\n')[1].decode('utf-8')
        print(f"Text content:\n{content}")
    elif content_disposition.startswith("attachment"):
        # Xử lý phần đính kèm
        filename = content_disposition.split('filename=')[1].strip('"')
        filename = f'{uid}_{filename}'
        save_attachment(part.split(b'\r\n\r\n')[1], filename)
        print(f"Saved attachment: {filename}")


def process_multipart(multipart_data, uid):
    boundary = multipart_data.split(b'\r\n')[0].decode(
        'utf-8').split('boundary=')[1].strip('"')
    parts = multipart_data.split(b'--' + boundary)[1:-1]

    for part in parts:
        process_part(part, uid)


def process_mime(email_content, uid):
    mime_index = email_content.find(b'Content-Type: multipart')
    if mime_index != -1:
        # Nếu có phần MIME
        mime_data = email_content[mime_index:]
        process_multipart(mime_data, uid)
    else:
        # Nếu không có phần MIME, xử lý nội dung trực tiếp
        process_part(email_content, uid)


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ip_address = socket.gethostbyname(POP3_SERVER)
        print(f"The IP address of {POP3_SERVER} is {ip_address}")
    except socket.gaierror as e:
        print(f"Error resolving {POP3_SERVER}: {e}")

    client_socket.connect((POP3_SERVER, POP3_PORT))

    client_socket.sendall(f'USER {USERNAME}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.sendall(f'PASS {PASSWORD}\r\n'.encode())
    response = client_socket.recv(1024).decode()
    print(response)

    downloaded_uids = read_uid_list()

    # Lấy danh sách UID
    client_socket.sendall(b'UIDL\r\n')
    response = client_socket.recv(1024).decode()
    uid_list_response = response.splitlines()[1:]
    print(uid_list_response)

    for uid_response in uid_list_response:
        uid = uid_response.split()[0]
        if uid not in downloaded_uids:
            email_content = download_email(uid, client_socket)

            # Xử lý MIME để trích xuất nội dung và đính kèm
            process_mime(email_content, uid)

            # Ghi nội dung email vào tệp
            file_path = os.path.join(DOWNLOAD_PATH, f'email_{uid}.txt')
            with open(file_path, 'w', encoding='utf-8') as email_file:
                email_file.write(email_content)

            downloaded_uids.add(uid)

    write_uid_list(downloaded_uids)

    client_socket.sendall(b'QUIT\r\n')
    response = client_socket.recv(1024).decode()
    print(response)

    client_socket.close()


if __name__ == "__main__":
    sendMail('seokjin@gmail.com')
    # Đọc trạng thái email từ file
    # email_state = load_email_state()

    # Bắt đầu thread tự động tải email
    # Lưu thời gian tải tự động được cài đặt trong file cấu hình
    # interval = int(config['Autoload']['interval'])
    # auto_fetch_thread = threading.Thread(
    #     target=auto_fetch_email, args=(interval, email_state))
    # auto_fetch_thread.start()

    # # Gửi/nhận email và xử lý trạng thái theo yêu cầu từ người dùng
    # # ...

    # # Chờ thread tự động tải email kết thúc khi thoát chương trình
    # auto_fetch_thread.join()

    # # Lưu trạng thái email khi tắt chương trình
    # save_email_state(email_state)
    main()
