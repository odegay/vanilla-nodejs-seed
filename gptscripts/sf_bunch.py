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
# SONAR_ORG_KEY = os.environ["SONAR_ORGANIZATION_KEY"]
# SONAR_PROJECT_KEY = os.environ["SONAR_PROJECT_KEY"]
# SONAR_TOKEN = os.environ["SONAR_TOKEN"]

# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# GITHUB_OWNER = os.environ["GITHUB_OWNER_ENV"]
# GITHUB_REPO_NAME = os.environ["GITHUB_REPO_NAME_ENV"]
# GITHUB_ACCESS_TOKEN = "os.environ['GITHUB_ACCESS_TOKEN_ENV']"

# DEV CONSTANTS
SONAR_ORG_KEY="odegay"
SONAR_PROJECT_KEY="odegay_vanilla-nodejs-seed"
SONAR_TOKEN="08dade2d05c5fc3eebfa6cf7be8247d314cec854"
OPENAI_API_KEY = "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"
GITHUB_OWNER = 'odegay'
GITHUB_REPO_NAME = 'vanilla-nodejs-seed'
GITHUB_ACCESS_TOKEN = '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'


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
        except requests.RequestException as e:
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
    return f"##### The SonarCloud found the following issues:\n{issues_text}\n \n### Code with issues\n{file_content}\n \n### Fixed Code that addresses all issues:"    

def generate_prompt(file_content, issue):
    #return f"Provide a code fix in the divide() function for the following issue in this code:\n\nIssue on line {issue['line']}: {issue['message']}\n\n---\n{file_content}\n---\n\nSuggested Fix:"
    #return f"\nGiven the following code:\n{file_content}\nProvide a fix for the following issue found by SonarCloud:{issue['message']}\nThe issue is located on line {issue['line']}\nSuggested Fix:"
    #return f"Issue: {issue}\n\n---\n{file_content}\n---\n\nSuggested Fix:"
    #return f"Please fix the issue in the divide() function in the given code snippet. The issue occurs on line {issue['line']} and is described as: {issue['message']}\n\n---\n{file_content}\n---\n\nProvide the corrected divide() function below:"
    return f"##### The SonarCloud found the following issue on line {issue['line']}: {issue['message']}\n \n### Code with issues\n{file_content}\n \n### Fixed Code that only contains fixed block of lines of code and not the entire code:"

def apply_suggested_fix(file_content, issue, suggested_fix):
    lines = file_content.split('\n')
    issue_line = issue['line'] - 1
    suggested_lines = suggested_fix.split('\n')

    # Calculate the range of lines affected by the issue
    affected_lines_range = range(issue_line, issue_line + len(suggested_lines))

    # Replace the affected lines with the suggested fix lines
    lines[issue_line : issue_line + len(suggested_lines)] = suggested_lines

    return '\n'.join(lines)

# Implement fixes using the GPT-4 API for all issues at once
def implement_fixes(issues_by_file):
    openai.api_key = OPENAI_API_KEY

    for file_path, issues in issues_by_file.items():
        # Read the file contents
        with open(file_path, 'r') as file:
            file_content = file.read()

        # Generate the prompt using the current file_content
        prompt = generate_all_issues_prompt(file_content, issues)
        print(f"Generating suggestion for the following file: {file_path}")
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=["###"]
            )
            suggested_fix = response.choices[0].text.strip()
            print(f"Suggested fix for issues '{issues}': {response}")
        except Exception as e:
            print(f"Error: Failed to get a suggestion from GPT-4 for issues '{issues}': {str(e)}")
            continue

        # Write the suggested fix directly back to the file
        with open(file_path, 'w') as file:
            file.write(suggested_fix)
            print(f"Updated file: {file_path}")

def create_pr(base, head, title):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO_NAME}/pulls"
    headers = {"Authorization": f"token {GITHUB_ACCESS_TOKEN}"}
    data = {
        "title": title,
        "head": head,
        "base": base,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()

def main():   

    # Create a temporary directory to clone the repo
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Clone the repo
        repo_url = f'https://{GITHUB_ACCESS_TOKEN}@github.com/{GITHUB_OWNER}/{GITHUB_REPO_NAME}.git'
        repo = Repo.clone_from(repo_url, tmp_dir, branch='master')

        # Set author identity for Git
        # repo.config_writer().set_value("user", "name", "odegay").release()
        # repo.config_writer().set_value("user", "email", "dolegan@gmail.com").release()

        repo.config_writer().set_value("user", "name", "robot").release()
        repo.config_writer().set_value("user", "email", "noreply@noreply.com").release()


        # Fetch issues from the SonarCloud API
        try:
            issues_by_file = fetch_issues(SONAR_TOKEN, tmp_dir)
        except Exception as e:
            print(f"Error: Failed to fetch issues from SonarCloud API: {str(e)}")
            sys.exit(1)

        # Create a new branch for the fixes with a unique name
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        new_branch_name = f"fixes_{current_time}"
        new_branch = repo.create_head(new_branch_name)

        # Checkout the new branch
        new_branch.checkout()

        # Implement fixes using the GPT-4 API
        try:
            implement_fixes(issues_by_file)
        except Exception as e:
            print(f"Error: Failed to implement fixes using GPT-4 API: {str(e)}")
            sys.exit(1)

        # Commit the changes
        repo.git.add(A=True)
        repo.git.commit(m='Apply automated fixes')

        # Push the changes to the new branch
        repo.git.push('--set-upstream', 'origin', new_branch.name)

    # Create a PR
    try:
        pr = create_pr('master', new_branch.name, 'Apply automated fixes')
        print(f"Created PR: {pr['html_url']}")
    except requests.RequestException as e:
        print(f"Error: Failed to create PR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()