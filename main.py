from __future__ import print_function
import os.path
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Define your filter keywords
keywords = [
    "internship", "job", "opportunity", "hiring", "selected", "shortlisted", "results", "application",
    "deadline", "placement", "interview", "resume", "cv", "career", "offer",
    "hackathon", "unstop", "winner", "result", "participation", "selection", "registration",
    "MongoDB", "LinkedIn", "TCS", "Wipro", "Infosys", "Accenture", "Google", "Microsoft"
]

def main():
    """Shows basic usage of the Gmail API.
    Lists the subject and sender of emails matching keywords.
    """
    creds = None

    # Load token.json if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there’s no token or it's invalid, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the Gmail service
    service = build('gmail', 'v1', credentials=creds)

    # Fetch recent 20 messages
    results = service.users().messages().list(userId='me', maxResults=20).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return

    print("Filtered Emails:\n" + "-" * 40)

    for msg in messages:
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()

        headers = msg_detail['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'No sender')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')

        # Check for keyword matches
        if any(kw.lower() in subject.lower() for kw in keywords):
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print("-" * 40)

if __name__ == '__main__':
    main()
