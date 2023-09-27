''' Export Jira issues '''
from pathlib import Path
import sys
import logging
import json
import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s')


class Jira:
    ''' Jira API wrapper '''

    def __init__(self, url: str, username: str, password: str) -> None:
        self.url = url
        self.username = username
        self.password = password

        self.session = requests.Session()
        self.session.auth = (username, password)

    def get_myself(self) -> dict | None:
        ''' Get information about the current user '''
        api = f'{self.url}/rest/api/latest/myself'
        result = self.session.get(api)
        return result.json() if result.status_code == 200 else None

    def export_issue(self, issue_key: str, dir_path: str | Path, file_type: str) -> None:
        ''' Save issue as doc '''
        match file_type:
            case 'xml':
                api = 'si/jira.issueviews:issue-xml'
            case 'doc' | _:
                api = 'si/jira.issueviews:issue-word'
                file_type = 'doc'

        issue_key = issue_key.strip()
        issue_url = f'{self.url}/{api}/{issue_key}/{issue_key}.{file_type}'
        result = self.session.get(issue_url)

        if result.status_code == 404:
            logging.warning("Can't export %s.%s", issue_key, file_type)
        else:
            Path(dir_path).mkdir(exist_ok=True, parents=True)
            with open(dir_path/f'{issue_key}.{file_type}', mode='wb') as file:
                file.write(result.content)
                logging.info('%s.%s saved', issue_key, file_type)


def main():
    ''' Entry point '''
    try:
        with open(Path(__file__).parent/'config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

        if config.keys() != {'url', 'email', 'token'}:
            raise KeyError
    except FileNotFoundError:
        sys.exit('config.json not found')
    except (json.decoder.JSONDecodeError, KeyError):
        sys.exit('Invalid config.json')

    output_dir = Path(__file__).parent/'output'
    issues_list = Path(__file__).parent/'issues.txt'

    if not issues_list.exists():
        sys.exit('issues.txt not found')

    jira = Jira(
        url=config['url'],
        username=config['email'],
        password=config['token'])

    if jira.get_myself() is None:
        sys.exit('Authentication error')

    with issues_list.open() as file:
        for issue in file:
            jira.export_issue(issue, output_dir, 'doc')
            jira.export_issue(issue, output_dir, 'xml')


if __name__ == '__main__':
    main()
