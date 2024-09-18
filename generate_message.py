import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
import openai

system_prompt = """You are a customer service representative
 tasked with responding to users question about the 
 services and other related queries."""

category_prompt = """You are an assistant that categorizes 
the user input into different categories and sub_categories"""

openai.api_key = ""
def save_message_text(email_dict, type):
    with open(email_dict['from'] + 'txt', 'a') as f:
        f.write(type + ': ')
        f.write('\n')
        f.write(email_dict['data'])
        f.write('\n')
        
def parse_parts(service, parts, messages, email_dct):

    if parts:
        for part in parts:
            filename = part.get('filename')
            mimeType = part.get('mimeType')
            body = part.get('body')
            data = body.get('data')
            file_size = body.get('size')
            part_headers = part.get("headers")
            if filename and mimeType and body and data:
                if mimeType == 'text/plain':
                    email_dct['data'] = data

                    save_message_text(email_dct, 'From user')
                else:
                    return None
    #                 file_data = urlsafe_b64decode(data).decode()
    #                 messages.append(f'Attachment: {filename} ({file_size} bytes)')
    # # return dct

def mark_as_read(service, message):
    service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()

def read_message(service, msg):
    email_dct = {}
    payload = msg['payload']
    headers = payload['headers']
    parts = payload.get('parts')
    has_subject = False
    if headers:
        for header in headers:
            name = header['name']
            value = header['value']
            if name.lower() == 'from':
                email_dct[name.lower()] = value
            if name.lower() == 'subject':
                has_subject = True
                email_dct[name.lower()] = value
            if name.lower() == 'to':
                email_dct[name.lower()] = value
    parse_parts(service, parts, msg, email_dct)
    return email_dct

def listening_to_inbox():
    pass

def response_GPT(email_dct):
    """
    This function uses the GPT-3.5-turbo model to
      generate a response to a user's question.
      category = {'category': 'Inquiry', 'sub_category': 'General'}"""
    category = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content":category_prompt},
                  {"role": "user", "content": email_dct['data']}],    
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content":system_prompt},
                  {"role": "user", "content": email_dct['data'], "category": category.choices[0].message['content']}],
    )
    mail = response.choices[0].message['content']
    save_message_text(mail, 'From system')
    return 
