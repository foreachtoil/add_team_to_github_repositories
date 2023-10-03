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
    url =  f'https://api.github.com/repos/{organization}/{repository}'
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
        return response.json()

    response = requests.post(
        response.json()['url'],
        json={
            'reviewers': reviewers,
            'team_reviewers': []
        },
        headers=headers
    )
    return {}



def main():
    parser = argparse.ArgumentParser(
        prog='Create GitHub PRs for a list of repositories to GitHub repositories',
        description='Allows creation of PRs for  individual or multiple Repositories with an individual or a list of approvers'
    )

    parser.add_argument(
        '-a',
        '--approvers',
        help='An individual GitHub team or the path to a file with a list of teams',
        required=True,
        metavar='approver/filename'
    )
    parser.add_argument(
        '-r',
        '--repositories',
        help='An individual GitHub repository or a file with a list of repositories',
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
        '-d',
        '--description',
        help='Description for the PR',
        default='Merging Develop branch to Test - Release to Staging'
    )
    parser.add_argument(
        '-h',
        '--head',
        help='Branch that will be the source of the changes',
    )
    parser.add_argument(
        '-b',
        '--base',
        help='Branch that will be the target of the changes',
    )
    args = parser.parse_args()

    headers = {
        'Authorization': f'token {args.github_token}'
    }

    try:
        approvers = open(args.approvers, 'r').read().splitlines()
    except FileNotFoundError:
        print(f'{args.approvers} is not a file, so targeting it as an individual group')
        approvers = [args.approvers]
    print(f'The amount of groups that will be added to the repositories is {len(teams)}')
    if args.repositories:
        try:
            repositories = open(args.repositories, 'r').read().splitlines()
        except FileNotFoundError:
            print(f'{args.repositories} is not a file, so targeting it as an individual repository')
            repositories = [args.repositories]
        print(f'The amount of target repositories is {len(repositories)}')

    print(f'Finding the Slug names for the teams')
    organization_teams = get_all_teams(args.organization, headers)
    team_ids = {}
    for team in organization_teams:
        team_ids[team['name']] = team['slug']

    for team in teams:
        print(f'Adding team {team} to {len(repositories)} repositories')
        for repository in repositories:
            add_team_to_repository(args.organization, repository, headers, team_ids[team], args.permission)


if __name__ == '__main__':
    main()