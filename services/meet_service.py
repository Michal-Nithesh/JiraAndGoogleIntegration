import requests

def create_meet_space(access_token):

    response = requests.post(
        "https://meet.googleapis.com/v2/spaces",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={}
    )

    return response.json()