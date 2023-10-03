import json
import time
import requests
import argparse



def create_pr_for_repository(
        organization,
        repository,
        headers,
        reviewers,
        title='Release to Test',
        body='Merging Develop branch to Test - Release to Staging',
        head='develop',
        base='test'):

    if 'pr' not in repository.keys():
        repository=repository['name']
        url = f'https://api.github.com/repos/{organization}/{repository}/pulls'
        print(url)
        response = requests.post(
            url,
            json={
                'title': title,
                'body': body,
                'head': head,
                'base': base
            },
            headers=headers
        )
        if response.status_code < 300:
            print(f'PR created for the repository {repository}')
        else:
            print(f'There was an issue creating the PR for the repository {repository}')
            print(response.json())
            return response.json()
        response = response.json()
        pr_url = response['url']
        html_url = response['html_url']
        creator_user = response['user']['login']
    else:
        print(f'Adding Owners to PR')
        pr_data = repository['pr']
        repository = repository['name']
        pr_get_url = f'https://api.github.com/repos/{organization}/{repository}/pulls/{pr_data}'
        response = requests.get(
            pr_get_url,
            headers=headers
        )
        response = response.json()
        try:
            pr_url = response['url']
            html_url = response['html_url']
            creator_user = response['user']['login']
        except KeyError:
            print(response)
            return response
    response = requests.post(
        f'{pr_url}/requested_reviewers',
        json={
            'reviewers': [reviewer for reviewer in reviewers if reviewer != creator_user],
            'team_reviewers': []
        },
        headers=headers
    )
    if response.status_code < 300:
        print(f'Reviews requested for PR {html_url}')
    else:
        print(f'There was an issue requesting the reviews for the PR {html_url}')
        return response.json() | { 'pr': html_url }
    return {
        'pr': html_url
    }

def main():
    parser = argparse.ArgumentParser(
        prog='Create GitHub PRs for a list of repositories to GitHub repositories',
        description='Allows creation of PRs for  individual or multiple Repositories with an individual or a list of approvers'
    )

    parser.add_argument(
        '-r',
        '--reviewer',
        help='An individual GitHub user or the path to a file with a list of users to be reviewers',
        required=True,
        metavar='reviewer/filename'
    )
    parser.add_argument(
        '-R',
        '--repositories',
        help='An individual GitHub repository or a file with a list of repositories',
        required=True,
        metavar='repository/filename'
    )
    parser.add_argument(
        '-o',
        '--organization',
        help='GitHub Organization if you want to add a group to all repositories within the Organization',
        required=True
    )
    parser.add_argument(
        '-g',
        '--github-token',
        help='GitHub Token for your user. You can get one here https://github.com/settings/tokens',
        required=True,
        metavar='token'
    )
    parser.add_argument(
        '-t',
        '--title',
        help='Title for the PR',
        default='Release to Test'
    )
    parser.add_argument(
        '-D',
        '--description',
        help='Description for the PR',
        default='Merging Develop branch to Test - Release to Staging'
    )
    parser.add_argument(
        '-s',
        '--source',
        help='Branch that will be the source of the changes',
        default='develop'
    )
    parser.add_argument(
        '-d',
        '--destination',
        help='Branch that will be the target of the changes',
        default='test'
    )
    parser.add_argument(
        '-P',
        '--patch',
        help='Splits the list of repositories by semi-colons ";" to target PRs',
        action='store_true'
    )
    args = parser.parse_args()

    headers = {
        'Authorization': f'token {args.github_token}'
    }

    try:
        reviewers = open(args.reviewer, 'r').read().splitlines()
    except FileNotFoundError:
        print(f'{args.reviewer} is not a file, so targeting it as an individual group')
        reviewers = [args.reviewer]
    print(f'The amount of reviewers that will be added to the PR is {len(reviewers)}')
    if args.repositories:
        try:
            repositories = open(args.repositories, 'r').read().splitlines()
            if args.patch:
                try:
                    repositories = [{'name': repository.split(';')[0], 'pr': repository.split(';')[1]} for repository in repositories]
                except IndexError:
                    print('Repositories should be separated by ";" [semi-colons] with the PRs to patch')
                    return 1
            else:
                repositories = [{'name': repository.split(';')[0]} for repository in repositories]
        except FileNotFoundError:
            print(f'{args.repositories} is not a file, so targeting it as an individual repository')
            repositories = [
                {'name': args.repositories.split(';')[0], 'pr': args.repositories.split(';')[1]} if args.patch else {'name': args.repositories}]
        print(f'The amount of target repositories is {len(repositories)}')
    prs = []
    for repository in repositories:
        print(f'Working on {repository["name"]} from {len(repositories)} repositories')
        response = create_pr_for_repository(
            args.organization,
            repository,
            headers,
            reviewers,
            args.title,
            args.description,
            args.source,
            args.destination
        )
        if response.get('pr'):
            prs.append(response['pr'])
    pr_str = [i + '\n' for i in prs]
    if pr_str:
        with open(f'prs_created{time.strftime("%Y%m%d-%H%M%S")}.txt', 'w+') as file:
            file.writelines(pr_str)
        print('List of PRs created:')
        for pr in pr_str:
            print(pr)
    else:
        print('No PR were fetched')

if __name__ == '__main__':
    main()