from flask import Flask, request, jsonify
from services.docs_service import create_document
from services.meet_service import create_meet_space
from services.jira_service import (
    create_jira_issue,
    list_jira_issues,
    add_comment,
    get_transitions,
    transition_issue,
    update_issue_fields,
    attach_file,
    search_assignable_users,
    assign_issue,
    get_link_types,
    link_issues,
    get_projects,
    get_issue_types,
    get_priorities,
    bulk_create_issues,
    get_board_view,
    search_issues
)
from services.calendar_service import create_calendar_event
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from services.gmail_service import create_gmail_draft
from services.gmail_service import (
    send_email,
    get_latest_email,
    get_unread_count
)
from services.drive_service import (
    create_folder,
    list_files
)
from services.sheets_service import create_sheet
load_dotenv()
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
JIRA_REDIRECT_URI = os.getenv("JIRA_REDIRECT_URI")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app = Flask(__name__)
CORS(app)

JIRA_ACCESS_TOKEN = None
JIRA_CLOUD_ID = None

GOOGLE_ACCESS_TOKEN = None

def require_jira():
    if not JIRA_ACCESS_TOKEN or not JIRA_CLOUD_ID:
        return jsonify({
            "success": False,
            "message": "Login Jira first",
            "login_url": "/jira/login"
        }), 401
    return None
@app.route("/")
def home():
    return {
        "app": "Adminii Integration",
        "status": "running"
    }
@app.route("/token-info")
def token_info():

    response = requests.get(
        f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={GOOGLE_ACCESS_TOKEN}"
    )

    return response.json()
@app.route("/jira/login")
def jira_login():

    auth_url = (
        "https://auth.atlassian.com/authorize"
        f"?audience=api.atlassian.com"
        f"&client_id={JIRA_CLIENT_ID}"
        f"&scope=read:jira-work write:jira-work read:jira-user offline_access"
        f"&redirect_uri={JIRA_REDIRECT_URI}"
        f"&response_type=code"
        f"&prompt=consent"
    )

    print(auth_url)
    return redirect(auth_url)
@app.route("/jira/callback")
def jira_callback():

    global JIRA_ACCESS_TOKEN
    global JIRA_CLOUD_ID

    code = request.args.get("code")

    if not code:
        return jsonify({
            "error": "authorization_code missing"
        })

    response = requests.post(
        "https://auth.atlassian.com/oauth/token",
        json={
            "grant_type": "authorization_code",
            "client_id": JIRA_CLIENT_ID,
            "client_secret": JIRA_CLIENT_SECRET,
            "code": code,
            "redirect_uri": JIRA_REDIRECT_URI
        }
    )

    token_data = response.json()

    if "access_token" not in token_data:
        return jsonify(token_data)

    JIRA_ACCESS_TOKEN = token_data["access_token"]

    headers = {
        "Authorization": f"Bearer {JIRA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }

    resources = requests.get(
        "https://api.atlassian.com/oauth/token/accessible-resources",
        headers=headers
    ).json()

    if resources:
        JIRA_CLOUD_ID = resources[0]["id"]

    return redirect(f"{FRONTEND_URL}/integrations?connected=jira")
@app.route("/login/google")
def login_google():

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope="
          "openid "
          "email "
          "profile "
          "https://www.googleapis.com/auth/calendar "
           "https://www.googleapis.com/auth/gmail.compose "
           "https://www.googleapis.com/auth/gmail.send "
           "https://www.googleapis.com/auth/gmail.readonly "
           "https://www.googleapis.com/auth/drive "
            "https://www.googleapis.com/auth/documents "
            "https://www.googleapis.com/auth/spreadsheets "
            "https://www.googleapis.com/auth/userinfo.email "
            "https://www.googleapis.com/auth/userinfo.profile "
        "&access_type=offline"
        "&prompt=consent"
    )

    return redirect(auth_url)
@app.route("/auth/google/callback")
def google_callback():

    global GOOGLE_ACCESS_TOKEN

    code = request.args.get("code")

    if not code:
        return jsonify({
            "error": "authorization_code missing"
        })

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    )

    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify(token_json)

    GOOGLE_ACCESS_TOKEN = token_json["access_token"]

    return redirect(f"{FRONTEND_URL}/integrations?connected=google")
@app.route("/status")
def status():
    return jsonify({
        "jira_connected": bool(JIRA_ACCESS_TOKEN),
        "google_connected": bool(GOOGLE_ACCESS_TOKEN)
    })
@app.route("/routes")
def routes():
    return {
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    }

@app.route("/jira/create", methods=["POST"])
def jira_create():

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    title = data.get("title")
    project_key = data.get("project_key", "KAN")
    issue_type = data.get("issue_type", "Task")

    result = create_jira_issue(
        title,
        JIRA_ACCESS_TOKEN,
        JIRA_CLOUD_ID,
        project_key,
        issue_type
    )

    return jsonify(result)
@app.route("/jira/issues")
def jira_issues():

    error = require_jira()
    if error:
        return error

    project_key = request.args.get("project", "KAN")

    result = list_jira_issues(
        JIRA_ACCESS_TOKEN,
        JIRA_CLOUD_ID,
        project_key
    )

    return jsonify(result)
@app.route("/jira/search")
def jira_search():

    error = require_jira()
    if error:
        return error

    jql = request.args.get("jql")
    if not jql:
        return jsonify({"success": False, "message": "jql query param is required"}), 400

    result = search_issues(
        jql,
        JIRA_ACCESS_TOKEN,
        JIRA_CLOUD_ID
    )

    return jsonify(result)
@app.route("/jira/projects")
def jira_projects():

    error = require_jira()
    if error:
        return error

    result = get_projects(JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue-types")
def jira_issue_types():

    error = require_jira()
    if error:
        return error

    project_key = request.args.get("project", "KAN")

    result = get_issue_types(project_key, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/priorities")
def jira_priorities():

    error = require_jira()
    if error:
        return error

    result = get_priorities(JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/bulk-create", methods=["POST"])
def jira_bulk_create():

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    titles = data.get("titles", [])
    project_key = data.get("project_key", "KAN")
    issue_type = data.get("issue_type", "Task")

    result = bulk_create_issues(titles, project_key, issue_type, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/board")
def jira_board():

    error = require_jira()
    if error:
        return error

    project_key = request.args.get("project", "KAN")

    result = get_board_view(project_key, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>/comment", methods=["POST"])
def jira_add_comment(issue_key):

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    result = add_comment(issue_key, data.get("comment"), JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>/transitions")
def jira_get_transitions(issue_key):

    error = require_jira()
    if error:
        return error

    result = get_transitions(issue_key, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>/transition", methods=["POST"])
def jira_transition_issue(issue_key):

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    result = transition_issue(issue_key, data.get("transition_id"), JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>", methods=["PUT"])
def jira_update_issue(issue_key):

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    result = update_issue_fields(issue_key, data, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>/attachment", methods=["POST"])
def jira_attach_file(issue_key):

    error = require_jira()
    if error:
        return error

    file_storage = request.files.get("file")
    if not file_storage:
        return jsonify({"success": False, "message": "file is required"}), 400

    result = attach_file(issue_key, file_storage, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/users")
def jira_users():

    error = require_jira()
    if error:
        return error

    project_key = request.args.get("project", "KAN")
    query = request.args.get("query", "")

    result = search_assignable_users(project_key, query, JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue/<issue_key>/assignee", methods=["PUT"])
def jira_assign_issue(issue_key):

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    result = assign_issue(issue_key, data.get("account_id"), JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/link-types")
def jira_link_types():

    error = require_jira()
    if error:
        return error

    result = get_link_types(JIRA_ACCESS_TOKEN, JIRA_CLOUD_ID)

    return jsonify(result)
@app.route("/jira/issue-link", methods=["POST"])
def jira_issue_link():

    error = require_jira()
    if error:
        return error

    data = request.get_json()

    result = link_issues(
        data.get("inward_key"),
        data.get("outward_key"),
        data.get("link_type"),
        JIRA_ACCESS_TOKEN,
        JIRA_CLOUD_ID
    )

    return jsonify(result)
@app.route("/workflow", methods=["POST"])
def workflow():

    global JIRA_ACCESS_TOKEN
    global JIRA_CLOUD_ID
    global GOOGLE_ACCESS_TOKEN

    if not JIRA_ACCESS_TOKEN:
        return jsonify({
            "success": False,
            "message": "Login Jira first",
            "login_url": "/jira/login"
        }), 401

    if not GOOGLE_ACCESS_TOKEN:
        return jsonify({
            "success": False,
            "message": "Login Google first",
            "login_url": "/login/google"
        }), 401

    data = request.get_json()

    title = data.get("title")
    due_date = data.get("due_date")

    try:

        jira_result = create_jira_issue(
            title,
            JIRA_ACCESS_TOKEN,
            JIRA_CLOUD_ID
        )

        calendar_result = create_calendar_event(
            title,
            due_date,
            GOOGLE_ACCESS_TOKEN
        )

        return jsonify({
            "success": True,
            "jira": jira_result,
            "calendar": calendar_result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/workflow/sprint-review", methods=["POST"])
def sprint_review():

    data = request.get_json()

    title = data.get("title", "Sprint Review")

    jira_result = create_jira_issue(
        title,
        JIRA_ACCESS_TOKEN,
        JIRA_CLOUD_ID
    )

    calendar_result = create_calendar_event(
        title,
        "2026-06-20T10:00:00+05:30",
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify({
        "success": True,
        "jira": jira_result,
        "calendar": calendar_result
    })
@app.route("/workflow/create-meeting", methods=["POST"])
def create_meeting():

    global JIRA_ACCESS_TOKEN
    global JIRA_CLOUD_ID
    global GOOGLE_ACCESS_TOKEN

    if not JIRA_ACCESS_TOKEN:
        return jsonify({
            "success": False,
            "message": "Login Jira first"
        }), 401

    if not GOOGLE_ACCESS_TOKEN:
        return jsonify({
            "success": False,
            "message": "Login Google first"
        }), 401

    data = request.get_json()

    title = data.get("title")
    meeting_date = data.get("date")
    attendees = data.get("attendees", [])

    try:

        # Create Jira Task
        jira_result = create_jira_issue(
            title,
            JIRA_ACCESS_TOKEN,
            JIRA_CLOUD_ID
        )

        # Create Calendar + Meet
        calendar_result = create_calendar_event(
            title,
            meeting_date,
            GOOGLE_ACCESS_TOKEN,
            attendees
        )

        meet_link = calendar_result.get("hangoutLink")

        # Create Gmail Draft
        email_body = f"""
Hi,

A meeting has been scheduled.

Title: {title}
Date: {meeting_date}

Google Meet:
{meet_link}

Regards,
Adminii
"""

        gmail_result = create_gmail_draft(
            f"{title} Meeting",
            email_body,
            GOOGLE_ACCESS_TOKEN
        )

        return jsonify({
            "success": True,
            "jira": jira_result,
            "calendar": calendar_result,
            "meet_link": meet_link,
            "gmail_draft": gmail_result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
@app.route("/test-meet")
def test_meet():
    result = create_calendar_event(
        "Adminii Meet Test",
        "2026-06-25T10:00:00+05:30",
        GOOGLE_ACCESS_TOKEN
    )

    return result
@app.route("/meet/create", methods=["POST"])
def create_meet():

    global GOOGLE_ACCESS_TOKEN

    if not GOOGLE_ACCESS_TOKEN:
        return jsonify({
            "success": False,
            "message": "Login Google first"
        }), 401

    result = create_meet_space(
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify(result)
@app.route("/gmail/send", methods=["POST"])
def gmail_send():

    data = request.get_json()

    to = data.get("to")
    subject = data.get("subject")
    message = data.get("message")

    result = send_email(
        GOOGLE_ACCESS_TOKEN,
        to,
        subject,
        message
    )

    return jsonify(result)
@app.route("/gmail/unread")
def gmail_unread():

    result = get_unread_count(
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify(result)


@app.route("/drive/create-folder", methods=["POST"])
def create_folder_route():

    data = request.get_json()

    folder_name = data.get("name")

    result = create_folder(
        folder_name,
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify(result)
@app.route("/docs/create", methods=["POST"])
def docs_create():

    data = request.get_json()

    result = create_document(
        data.get("title"),
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify(result)
@app.route("/sheets/create", methods=["POST"])
def sheets_create():

    data = request.get_json()

    result = create_sheet(
        data.get("title"),
        GOOGLE_ACCESS_TOKEN
    )

    return jsonify(result)
if __name__ == "__main__":
    app.run(debug=True)