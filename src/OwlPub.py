import json
from os.path import abspath, join, splitext, basename, realpath, dirname

from RepoHandler import RepoHandler


class ParseConfigError(Exception):
    def __init__(self, arg):
        super(ParseConfigError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class RepositoryNotFoundError(Exception):
    def __init__(self, arg):
        super(RepositoryNotFoundError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class OwlPub:
    repos = []

    def __init__(self):
        self.load_config()

    def load_config(self):
        config_path = join(dirname(realpath(__file__)), 'config',
                           'config.json')

        with open(config_path) as config_file:
            config = json.load(config_file)

        dir_repos = abspath(config['directories']['repos'])
        dir_web = abspath(config['directories']['web'])

        for repo in config['repos']:
            repo_config = self.parse_repo_config(repo, dir_repos, dir_web)
            self.repos.append(repo_config)

        try:
            pass
        except:
            raise ParseConfigError(u'config file invalid')

    def parse_repo_config(self, config, dir_repos, dir_web):
        repo_name = splitext(basename(config['clone_url']))[0]
        dir_repo = join(dir_repos, repo_name)

        repo_config = {
            'directory': dir_repo,
            'clone_url': config['clone_url'],
            'webhook_id': config['webhook_id']
            if 'webhook_id' in config else None,
            'secret': config['secret'] if 'secret' in config else None,
            'ontologies': [self.parse_ontology_config(ontology,
                                                      dir_repo,
                                                      dir_web)
                           for ontology in config['ontologies']]
        }

        return repo_config

    @staticmethod
    def parse_ontology_config(config, dir_repo, dir_web):
        return {
            'ontology': join(dir_repo, config['ontology']),
            'template': join(dir_repo, config['template'])
            if 'template' in config else None,
            'web_directory': join(dir_web, config['directory'])
        }

    def get_repo_by_webhook_id(self, webhook_id):
        for repo_config in self.repos:
            if repo_config['webhook_id'] == webhook_id:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError(
            u'repository with webhook_id ' + str(webhook_id) + u' not found!')

    def get_repo_by_name(self, name):
        for repo_config in self.repos:
            if name + '.git' in repo_config['clone_url']:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError(
            u'repository with name ' + str(name) + u' not found!')

    def rise(self):
        for repo_config in self.repos:
            repo = RepoHandler(repo_config)
            repo.regenerate()


if __name__ == '__main__':
    publisher = OwlPub()
    publisher.rise()
