import requests
import base64


def create_gmail_draft(subject, body, access_token):

    message = f"""Subject: {subject}

{body}
"""

    encoded_message = base64.urlsafe_b64encode(
        message.encode()
    ).decode()

    payload = {
        "message": {
            "raw": encoded_message
        }
    }

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    return response.json()


def send_email(access_token, to, subject, message):

    email_message = f"""To: {to}
Subject: {subject}

{message}
"""

    encoded_message = base64.urlsafe_b64encode(
        email_message.encode()
    ).decode()

    payload = {
        "raw": encoded_message
    }

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    return response.json()


def get_latest_email(access_token):

    response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response.json()


def get_unread_count(access_token):

    response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels/UNREAD",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response.json()