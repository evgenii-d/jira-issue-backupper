''' Jira Issue Backupper '''
from pathlib import Path
import sys
import logging
import json
import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')


def save_issue(jira_url: str, jira_auth: str, issue: str,
               file_type: str, output_dir: str | Path):
    ''' Save issue as file '''
    issue_key = issue.strip()
    file_name = f'{issue_key}.{file_type}'

    match file_type:
        case 'doc':
            api = 'si/jira.issueviews:issue-word'
        case 'xml':
            api = 'si/jira.issueviews:issue-xml'

    issue_url = f'{jira_url}/{api}/{issue_key}/{issue_key}.{file_type}'
    request = requests.get(issue_url, auth=jira_auth, timeout=10)

    if request.status_code == 404:
        logging.warning("Can't save %s", issue_key)
    else:
        with open(output_dir/file_name, mode='wb') as file:
            file.write(request.content)
            logging.info('%s saved', file_name)


def main():
    ''' Entry point '''
    try:
        config_path = Path(__file__).parent/'config.json'
        config_keys = {'url', 'email', 'token'}

        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        if config.keys() != config_keys:
            raise KeyError
    except FileNotFoundError:
        sys.exit('config.json not found')
    except (json.decoder.JSONDecodeError, KeyError):
        sys.exit('invalid config.json')

    jira_auth = (config['email'], config['token'])
    jira_url = config['url']
    check_api = f'{jira_url}/rest/api/latest/myself'

    output_dir = Path(__file__).parent/'output'
    issues_list = Path(__file__).parent/'issues.txt'

    if not issues_list.exists():
        sys.exit('issues.txt not found')

    request = requests.get(check_api, auth=jira_auth, timeout=10)
    if request.status_code != 200:
        sys.exit('Authentication error')

    Path(output_dir).mkdir(exist_ok=True, parents=True)
    with issues_list.open() as file:
        for issue in file:
            save_issue(jira_url, jira_auth, issue, 'doc', output_dir)
            save_issue(jira_url, jira_auth, issue, 'xml', output_dir)


if __name__ == '__main__':
    main()
