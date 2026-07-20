import requests


def create_folder(folder_name, access_token):

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }

    response = requests.post(
        "https://www.googleapis.com/drive/v3/files",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=metadata
    )

    return response.json()


def list_files(access_token):

    response = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    return response.json()