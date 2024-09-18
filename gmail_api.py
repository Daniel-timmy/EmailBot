import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.message import EmailMessage
from googleapiclient.errors import HttpError
from time import sleep
import logging
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
from generate_message import read_message, response_GPT, mark_as_read

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'ajayitimmy45@gmail.com'


def gmail_authenticate():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow =InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = EmailMessage()
    message['To'] = to
    message['Rrom'] = sender
    message['Subject'] = subject
    message.set_content(message_text)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, sender, to, subject, message):
    """Send an email message."""
    try:
        message = (service.users()
                   .messages()
                   .send(userId='me',body=create_message(sender, to, subject, message))
                   .execute())
        print('Message Id: %s' % message['id'])
        return message
    except Exception as e:
        print('An error occurred: %s' % e)
        return None
    
def search_messages(service, query):
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', q=query, page_token=page_token).execute()
        messages.extend(result['messages'])
    return messages

def get_message(service, msg_id):
    return service.users().messages().get(userId='me', id=msg_id, format='full').execute()


if __name__ == '__main__':
    service = gmail_authenticate()

    # search for all unread messages
    while True:
        try:
            query = 'is:unread'
            messages = search_messages(service, query)

            # read each message and extract all the important information
            for message in messages:
                email_dict = read_message(service, message)
                response = response_GPT(email_dict)
                msg = send_message(sender=email_dict['from'], to=email_dict['to'], subject=email_dict['subject'], message=response)
                mark_as_read(service, message)
        except (HttpError, FileNotFoundError) as error:
            logging.basicConfig(filename="error.log",
                encoding='utf-8',
                filemode='a',
                format='(asctime) - (message)',
                style="{",
                level=logging.ERROR,
                datefmt="%d-%m-%Y %H:%M",
            )
            
        sleep(3600)