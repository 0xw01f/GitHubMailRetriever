# GitHub Email Retriever

An OSINT tool to extract email addresses associated with a GitHub user's public activity on GitHub.

## Features

- Retrieves public repositories and events for a given GitHub username
- Extracts email addresses from commit patches and event data
- Validates and normalizes extracted email addresses
- Filters out GitHub-provided emails
- Saves results to a CSV file with email, repository, and commit information
- Displays unique emails and their occurrence counts

## Requirements

- Python 3.7+
- aiohttp
- asyncio
- pandas
- python-dotenv
- email-validator

## Installation

1. Clone this repository
2. Install required packages: `pip install -r requirements.txt`
3. Create a `.env` file in the project directory and add your GitHub token:
`GITHUB_TOKEN=your_github_token_here`

## Usage

Run the script with the following command:
`python script.py -u <github_username>`

Replace `<github_username>` with the target GitHub username.

## Output

- Extracted emails are saved to `emails.csv`
- Unique emails and their counts are displayed in the console

## Disclaimer

This tool is for educational and research purposes only. Always respect privacy and adhere to applicable laws and regulations when using OSINT tools.
