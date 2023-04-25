import os
import requests
import json
import openai
import base64
import sys
import subprocess
import tempfile
from git import Repo
from datetime import datetime

SONAR_API_URL = "https://sonarcloud.io/api"
# PROD CONSTANTS
SONAR_ORG_KEY = os.environ["SONAR_ORGANIZATION_KEY"]
SONAR_PROJECT_KEY = os.environ["SONAR_PROJECT_KEY"]
SONAR_TOKEN = os.environ["SONAR_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GITHUB_OWNER = os.environ["GITHUB_OWNER_ENV"]
GITHUB_REPO_NAME = os.environ["GITHUB_REPO_NAME_ENV"]
GITHUB_ACCESS_TOKEN = "os.environ['GITHUB_ACCESS_TOKEN_ENV']"

def fetch_issues(sonar_token, source_directory):
    SONAR_API_BASE_URL = "https://sonarcloud.io/api"
    ORGANIZATION_KEY = SONAR_ORG_KEY
    PROJECT_KEY = SONAR_PROJECT_KEY

    auth_header = base64.b64encode(f"{sonar_token}:".encode()).decode()

    # Define the function to fetch issues from the SonarCloud API
    def fetch_paged_issues(page_index):
        try:
            response = requests.get(
                f"{SONAR_API_BASE_URL}/issues/search",
                params={
                    "organization": ORGANIZATION_KEY,
                    "projects": PROJECT_KEY,
                    "types": "CODE_SMELL, BUG, VULNERABILITY",
                    "statuses": "OPEN, CONFIRMED, REOPENED",
                    "p": page_index,
                },
                headers={"Authorization": f"Basic {auth_header}"},
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise Exception(f"Error: Failed to fetch issues from SonarCloud API: {str(e)}")

    # Fetch all pages of issues
    issues_by_file = {}
    page_index = 1
    while True:
        try:
            result = fetch_paged_issues(page_index)
        except Exception as e:
            print(e)
            sys.exit(1)

        issues = result["issues"]

        if not issues:
            break

        for issue in issues:
            # Remove the project key from the component
            file_path = issue["component"].replace(SONAR_PROJECT_KEY + ":", "")
            file_path = os.path.join(source_directory, file_path)
            line = issue.get("line", 0)
            message = issue["message"]

            if file_path not in issues_by_file:
                issues_by_file[file_path] = []

            issues_by_file[file_path].append({
                "line": line,
                "message": message,
        })

        page_index += 1

    return issues_by_file

# Generate the prompt for fixing all issues at once
def generate_all_issues_prompt(file_content, issues):
    issues_text = "\n".join([f"Line {issue['line']}: {issue['message']}" for issue in issues])
    return f"