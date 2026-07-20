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

    headers = {"Authorization": f"Bearer {access_token}"}

    list_response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=headers,
        params={"maxResults": 1}
    )

    list_data = list_response.json()
    messages = list_data.get("messages", [])

    if not messages:
        return {"message": None}

    message_id = messages[0]["id"]

    detail_response = requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
        headers=headers,
        params={"format": "metadata", "metadataHeaders": ["Subject", "From"]}
    )

    detail = detail_response.json()
    header_map = {
        h["name"]: h["value"]
        for h in detail.get("payload", {}).get("headers", [])
    }

    return {
        "message": {
            "id": message_id,
            "subject": header_map.get("Subject", "(no subject)"),
            "from": header_map.get("From", "Unknown sender"),
            "snippet": detail.get("snippet", "")
        }
    }


def get_unread_count(access_token):

    response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels/UNREAD",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response.json()