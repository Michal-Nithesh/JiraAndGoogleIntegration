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


def list_files(access_token, page_size=10):

    response = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        params={
            "pageSize": page_size,
            "orderBy": "modifiedTime desc",
            "fields": "files(id,name,mimeType,webViewLink,modifiedTime)"
        }
    )

    return response.json()