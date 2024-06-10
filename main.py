import aiohttp
import asyncio
import pandas as pd
from dotenv import dotenv_values
import sys
from email_validator import validate_email, EmailNotValidError
import re

# Load environment variables from .env file
env_values = dotenv_values('.env')
GITHUB_TOKEN = env_values.get('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN is missing in the .env file.")
    exit(1)

# GitHub API URLs
REPOS_URL = 'https://api.github.com/users/{}/repos'
COMMITS_URL = 'https://api.github.com/repos/{owner}/{repo}/commits'
EVENTS_URL = 'https://api.github.com/users/{}/events/public'

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def get_user_repositories(username, token):
    async with aiohttp.ClientSession() as session:
        async with session.get(REPOS_URL.format(username), headers={'Authorization': f'token {token}'}) as response:
            return await response.json()

async def get_user_events(username, token):
    async with aiohttp.ClientSession() as session:
        async with session.get(EVENTS_URL.format(username), headers={'Authorization': f'token {token}'}) as response:
            return await response.json()

async def get_repository_commits(session, owner, repo, token):
    url = COMMITS_URL.format(owner=owner, repo=repo)
    async with session.get(url, headers={'Authorization': f'token {token}'}) as response:
        commits = await response.json()
        return [commit['html_url'] for commit in commits]

async def extract_matches_from_patch(session, url, token):
    patch_url = url + '.patch'
    async with session.get(patch_url, headers={'Authorization': f'token {token}'}) as response:
        patch_content = await response.text()
        emails = re.findall(r'<(.+@.+\..+)>', patch_content)
        valid_emails = []

        for email in emails:
            try:
                emailinfo = validate_email(email, check_deliverability=False)
                normalized_email = emailinfo.normalized
                if not normalized_email.endswith("github.com"):
                    valid_emails.append(normalized_email)
            except EmailNotValidError:
                continue
        
        return valid_emails

async def process_repo(session, repo, token, emailsWRepo):
    try:
        owner = repo['owner']['login']
        repo_name = repo['name']
        commit_links = await get_repository_commits(session, owner, repo_name, token)
        for link in commit_links:
            matches = await extract_matches_from_patch(session, link, token)
            for match in matches:
                print(f"Found email: {match} in {repo_name}")
                emailsWRepo.append([match, repo_name, link])
    except Exception as e:
        print(f"An error occurred: {str(e)}")

async def process_events(events, emailsWRepo):
    for event in events:
        if 'payload' in event and 'commits' in event['payload']:
            for commit in event['payload']['commits']:
                if 'author' in commit and 'email' in commit['author']:
                    email = commit['author']['email']
                    try:
                        emailinfo = validate_email(email, check_deliverability=False)
                        normalized_email = emailinfo.normalized
                        if not normalized_email.endswith("github.com"):
                            print(f"Found email: {normalized_email} in event {event['id']}")
                            emailsWRepo.append([normalized_email, 'event', event['id']])
                    except EmailNotValidError:
                        continue

async def main():
    if len(sys.argv) < 2 or sys.argv[1] != '-u':
        print("Usage: python script.py -u <github_username>")
        return

    if len(sys.argv) < 3:
        print("Error: GitHub username is missing.")
        return

    username = sys.argv[2]
    emailsWRepo = []
    try:
        repositories = await get_user_repositories(username, GITHUB_TOKEN)
        events = await get_user_events(username, GITHUB_TOKEN)
        
        async with aiohttp.ClientSession() as session:
            repo_tasks = [process_repo(session, repo, GITHUB_TOKEN, emailsWRepo) for repo in repositories]
            await asyncio.gather(*repo_tasks)
        
        await process_events(events, emailsWRepo)

        df = pd.DataFrame(emailsWRepo, columns=['Email', 'Repo', 'Commit'])
        df.to_csv('emails.csv', index=False)

        # Print the unique emails and their counts
        print("\nUnique emails and their counts:")
        print(df['Email'].value_counts())
        print("\nFull output with affected repository names and commit links is saved to the emails.csv file.")  

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
