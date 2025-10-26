import json, os, urllib.request, urllib.error
from datetime import datetime

OWNER = os.getenv("GITHUB_OWNER")
REPO  = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
Q_LABEL = "Amazon Q development agent"
UA = "quietops-lambda/1.0"

def gh_post(url, payload, timeout=15):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": UA
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise Exception(f"GitHub HTTP {e.code}: {body}")

def gh_get(url, timeout=10):
    req = urllib.request.Request(
        url, headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": UA
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def lambda_handler(event, context):
    # sanity check token
    code, me = gh_get("https://api.github.com/user")
    if code != 200:
        raise Exception(f"Token unusable: HTTP {code} {me}")

    # Parse the nested incident_input structure
    incident_input = event.get("incident_input", {})
    
    # Extract incident time from the first alarm or use current time
    alarms = incident_input.get("alarms", [])
    if alarms and "StateChangeTime" in alarms[0]:
        incident_time = alarms[0]["StateChangeTime"]
    else:
        incident_time = datetime.utcnow().isoformat() + "Z"
    
    # Extract likely files from deploy information
    deploy_info = incident_input.get("deploy", {})
    likely_files = deploy_info.get("changed_files", [])
    
    # Build error summary from alarms and logs
    error_summary = {
        "alarms": alarms,
        "logs": incident_input.get("logs", []),
        "deploy": deploy_info
    }

    body = (
        "[QuietOps] Automated incident\n\n"
        f"Time: {incident_time}\n"
        f"Likely files: {likely_files}\n\n"
        "Cleaned errors:\n```json\n"
        f"{json.dumps(error_summary, indent=2)}\n"
        "```\n\nParse the user's code and identify where the errors in the codebase are based on the errors that are provided. If the errors are unrelated to the repository at all, do not submit a PR. If they are related, figure out how to properly update the code thoroughly and open a Draft PR against `main`."
    )

    # ensure label exists (ignore if already there)
    try:
        gh_post(f"https://api.github.com/repos/{OWNER}/{REPO}/labels",
                {"name": Q_LABEL, "color": "1f883d"})
    except Exception:
        pass

    # create issue (triggers Q)
    status, issue = gh_post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/issues",
        {"title": "[QuietOps] Fix errors after deploy", "body": body, "labels": [Q_LABEL]}
    )
    return {"issue_url": issue["html_url"], "issue_number": issue["number"]}