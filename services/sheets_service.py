import requests


def create_sheet(title, access_token):

    response = requests.post(
        "https://sheets.googleapis.com/v4/spreadsheets",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "properties": {
                "title": title
            }
        }
    )

    return response.json()