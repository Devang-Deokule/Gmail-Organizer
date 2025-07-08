from __future__ import print_function
import os.path
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Full Gmail access for reading and labeling
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_or_create_label(service, label_name):
    existing_labels = service.users().labels().list(userId='me').execute()
    for label in existing_labels['labels']:
        if label['name'].lower() == label_name.lower():
            return label['id']
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created_label = service.users().labels().create(userId='me', body=label_object).execute()
    return created_label['id']

# Label keywords
label_keywords = {
    "Jobs": ["job", "opportunity", "hiring", "career", "placement", "offer"],
    "Internships": ["internship", "training", "intern"],
    "Hackathons": ["hackathon", "unstop", "devpost", "solution", "submission", "winner"],
    "Interviews": ["interview", "shortlisted", "selected", "round"],
    "Results": ["result", "qualified", "merit", "score", "ranking"],
    "Companies": ["MongoDB", "Google", "Microsoft", "Infosys", "TCS", "Wipro", "LinkedIn"],
    "Spam": ["win", "prize", "congratulations", "gift", "click", "free", "claim", "offer", "credit", "loan", "bonus", "cheap", "urgent", "guaranteed", "bitcoin", "hot deal"]
}

# Optional spammy sender patterns
spam_senders = ["@loan", "@promo", ".xyz", "@click", "@maildeal", "@noreply.cash"]

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        maxResults=100,
        q=""
    ).execute()
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

        # ⚠️ First: Check for spam
        if any(s.lower() in sender.lower() for s in spam_senders) or \
           any(k.lower() in subject.lower() for k in label_keywords["Spam"]):
            print(f"[Spam] From: {sender}")
            print(f"Subject: {subject}")
            print("-" * 40)
            spam_label_id = get_or_create_label(service, "Spam")
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'addLabelIds': [spam_label_id]}
            ).execute()
            continue  # Skip rest of labels if marked spam

        # ✅ Then: Check all other categories
        for label, kw_list in label_keywords.items():
            if label == "Spam":
                continue  # Already handled above
            if any(k.lower() in subject.lower() for k in kw_list):
                print(f"[{label}] From: {sender}")
                print(f"Subject: {subject}")
                print("-" * 40)

                label_id = get_or_create_label(service, label)
                service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'addLabelIds': [label_id]}
                ).execute()
                break  # Only one label per message

if __name__ == '__main__':
    main()
