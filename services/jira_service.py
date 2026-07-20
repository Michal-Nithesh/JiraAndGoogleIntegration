import requests

def _headers(access_token, content_type=True):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    if content_type:
        headers["Content-Type"] = "application/json"
    return headers

def text_to_adf(text):
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}] if text else []
            }
        ]
    }

def get_current_account_id(access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself",
        headers=headers
    )

    if response.status_code == 200:
        return response.json().get("accountId")

    return None

def create_jira_issue(
    title,
    access_token,
    cloud_id,
    project_key="KAN",
    issue_type="Task"
):

    headers = _headers(access_token)

    account_id = get_current_account_id(access_token, cloud_id)

    fields = {
        "project": {
            "key": project_key
        },
        "summary": title,
        "issuetype": {
            "name": issue_type
        }
    }

    if account_id:
        fields["assignee"] = {"accountId": account_id}

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue",
        headers=headers,
        json={"fields": fields}
    )

    return response.json()

def search_issues(jql, access_token, cloud_id, max_results=20):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql",
        headers=headers,
        params={
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,status,assignee,created"
        }
    )

    data = response.json()

    issues = [
        {
            "key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "status": issue.get("fields", {}).get("status", {}).get("name"),
            "assignee": (issue.get("fields", {}).get("assignee") or {}).get("displayName"),
            "created": issue.get("fields", {}).get("created")
        }
        for issue in data.get("issues", [])
    ]

    return {"issues": issues}

def list_jira_issues(access_token, cloud_id, project_key="KAN"):
    return search_issues(
        f"project = {project_key} ORDER BY created DESC",
        access_token,
        cloud_id
    )

def add_comment(issue_key, comment_text, access_token, cloud_id):
    headers = _headers(access_token)

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/comment",
        headers=headers,
        json={"body": text_to_adf(comment_text)}
    )

    return response.json()

def get_transitions(issue_key, access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/transitions",
        headers=headers
    )

    data = response.json()

    return {
        "transitions": [
            {"id": t.get("id"), "name": t.get("name")}
            for t in data.get("transitions", [])
        ]
    }

def transition_issue(issue_key, transition_id, access_token, cloud_id):
    headers = _headers(access_token)

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/transitions",
        headers=headers,
        json={"transition": {"id": transition_id}}
    )

    if response.status_code == 204:
        return {"success": True}

    return response.json()

def update_issue_fields(issue_key, updates, access_token, cloud_id):
    headers = _headers(access_token)

    fields = {}

    if updates.get("description") is not None:
        fields["description"] = text_to_adf(updates["description"])

    if updates.get("priority"):
        fields["priority"] = {"name": updates["priority"]}

    if updates.get("due_date"):
        fields["duedate"] = updates["due_date"]

    if updates.get("labels") is not None:
        fields["labels"] = updates["labels"]

    response = requests.put(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}",
        headers=headers,
        json={"fields": fields}
    )

    if response.status_code == 204:
        return {"success": True}

    return response.json()

def attach_file(issue_key, file_storage, access_token, cloud_id):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "X-Atlassian-Token": "no-check"
    }

    files = {
        "file": (file_storage.filename, file_storage.stream, file_storage.mimetype)
    }

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/attachments",
        headers=headers,
        files=files
    )

    return response.json()

def search_assignable_users(project_key, query, access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/user/assignable/search",
        headers=headers,
        params={"project": project_key, "query": query or ""}
    )

    data = response.json()

    if not isinstance(data, list):
        return {"users": []}

    return {
        "users": [
            {"accountId": u.get("accountId"), "displayName": u.get("displayName")}
            for u in data
        ]
    }

def assign_issue(issue_key, account_id, access_token, cloud_id):
    headers = _headers(access_token)

    response = requests.put(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}/assignee",
        headers=headers,
        json={"accountId": account_id}
    )

    if response.status_code == 204:
        return {"success": True}

    return response.json()

def get_link_types(access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issueLinkType",
        headers=headers
    )

    data = response.json()

    return {
        "link_types": [
            {"name": lt.get("name"), "inward": lt.get("inward"), "outward": lt.get("outward")}
            for lt in data.get("issueLinkTypes", [])
        ]
    }

def link_issues(inward_key, outward_key, link_type_name, access_token, cloud_id):
    headers = _headers(access_token)

    response = requests.post(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issueLink",
        headers=headers,
        json={
            "type": {"name": link_type_name},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
    )

    if response.status_code == 201:
        return {"success": True}

    return response.json()

def get_projects(access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/search",
        headers=headers
    )

    data = response.json()

    return {
        "projects": [
            {"key": p.get("key"), "name": p.get("name"), "id": p.get("id")}
            for p in data.get("values", [])
        ]
    }

def get_issue_types(project_key, access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/createmeta",
        headers=headers,
        params={"projectKeys": project_key, "expand": "projects.issuetypes"}
    )

    data = response.json()
    projects = data.get("projects", [])

    if not projects:
        return {"issue_types": []}

    issue_types = projects[0].get("issuetypes", [])

    return {
        "issue_types": [
            {"id": it.get("id"), "name": it.get("name")}
            for it in issue_types
            if not it.get("subtask")
        ]
    }

def get_priorities(access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/priority",
        headers=headers
    )

    data = response.json()

    if not isinstance(data, list):
        return {"priorities": []}

    return {
        "priorities": [{"name": p.get("name")} for p in data]
    }

def bulk_create_issues(titles, project_key, issue_type, access_token, cloud_id):
    created = []
    failed = []

    for title in titles:
        result = create_jira_issue(title, access_token, cloud_id, project_key, issue_type)
        if result.get("key"):
            created.append(result)
        else:
            failed.append({"title": title, "error": result})

    return {"created": created, "failed": failed}

def _group_issues_by_status(issues):
    columns = {}
    for issue in issues:
        fields = issue.get("fields", {})
        status_name = fields.get("status", {}).get("name", "Unknown")
        columns.setdefault(status_name, []).append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "assignee": (fields.get("assignee") or {}).get("displayName")
        })
    return columns

def get_board_view(project_key, access_token, cloud_id):
    headers = _headers(access_token, content_type=False)

    boards_response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/board",
        headers=headers,
        params={"projectKeyOrId": project_key}
    )

    boards = boards_response.json().get("values", [])

    if not boards:
        return {"columns": {}, "message": "No board found for this project"}

    board_id = boards[0]["id"]

    sprints_response = requests.get(
        f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/board/{board_id}/sprint",
        headers=headers,
        params={"state": "active"}
    )

    active_sprints = sprints_response.json().get("values", []) if sprints_response.status_code == 200 else []

    if active_sprints:
        sprint_id = active_sprints[0]["id"]
        issues_response = requests.get(
            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/sprint/{sprint_id}/issue",
            headers=headers
        )
    else:
        issues_response = requests.get(
            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/board/{board_id}/issue",
            headers=headers
        )

    issues = issues_response.json().get("issues", [])

    return {"columns": _group_issues_by_status(issues)}
