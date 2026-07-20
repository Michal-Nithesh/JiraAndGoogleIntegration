import requests


def create_document(title, access_token):

    response = requests.post(
        "https://docs.googleapis.com/v1/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "title": title
        }
    )

    return response.json()