#!/usr/bin/python3 -B
# coding=utf-8

import json
from os.path import abspath, join, splitext, basename, realpath, dirname, exists

from jinja2 import Environment

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
    _all_repos = []
    _dir_web = None
    _dir_repos = None
    _template_index = None

    def __init__(self):
        self.__load_config()

    def __load_config(self):
        try:
            config_path = join(dirname(realpath(__file__)), 'config.json')

            with open(config_path) as config_file:
                config = json.load(config_file)

            try:
                self._dir_repos = abspath(config['directories']['repos_dir'])
            except KeyError:
                self._dir_repos = abspath('repos')

            try:
                self._dir_web = abspath(config['directories']['web_dir'])
            except KeyError:
                self._dir_web = abspath('webroot')

            self._template_index = config['template_index'] \
                if 'template_index' in config else None

            for repo in config['repos']:
                repo_config = self.__parse_repo_config(repo)
                self._all_repos.append(repo_config)
        except:
            raise ParseConfigError('Configs file invalid')

    def __parse_repo_config(self, config):
        repo_name = splitext(basename(config['clone_url']))[0]
        dir_repo = join(self._dir_repos, repo_name)

        repo_config = {
            'directory': dir_repo,
            'clone_url': config['clone_url'],
            'webhook_id': int(config['webhook_id'])
            if 'webhook_id' in config and int(config['webhook_id']) > 0
            else None,
            'secret': config['secret'] if 'secret' in config else None,
            'ontologies': [self.__parse_ontology_config(ontology, dir_repo)
                           for ontology in config['ontologies']]
        }

        return repo_config

    def __parse_ontology_config(self, config, dir_repo):
        return {
            'ontology': join(dir_repo, config['ontology']),
            'template': join(dir_repo, config['template'])
            if 'template' in config else None,
            'webname_dir': join(self._dir_web, config['webname_dir'])
        }

    def get_repo_by_webhook_id(self, webhook_id):
        for repo_config in self._all_repos:
            if repo_config['webhook_id'] == webhook_id:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError('Repository with webhook ID {} not found!'
                                      .format(webhook_id))

    def get_repo_by_name(self, name):
        for repo_config in self._all_repos:
            if name + '.git' in repo_config['clone_url']:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError('Repository with name "{}" not found!'
                                      .format(name))

    def run(self):
        # Data for index file
        index_data = []

        # Do some stuff with all repos
        for repo_config in self._all_repos:
            # Generate documentation for ontology
            repo = RepoHandler(repo_config)
            repo.regenerate()

            # Collect data for index file
            # TODO: Make moar pretty
            index_data_ontologies = []
            for ontology in repo_config['ontologies']:
                name = splitext(basename(ontology['ontology']))[0]
                path = ontology['webname_dir'].replace(
                    self._dir_web, ''
                )[1:] + '/' + name
                index_data_ontologies.append({
                    'path': path,
                    'name': name
                })

            index_data.append({
                'repo_name': repo_config['clone_url'].replace(
                    'https://github.com/', ''
                ),
                'ontologies': index_data_ontologies
            })

        # Generate index file
        if self._template_index is None or not exists(self._template_index):
            template_index_path = join(
                dirname(realpath(__file__)), 'templates', 'default-index.html'
            )
        else:
            template_index_path = self._template_index

        env = Environment(trim_blocks=True, lstrip_blocks=True)
        with open(template_index_path, 'r') as template_index_file:
            template = env.from_string(template_index_file.read())
        with open(join(self._dir_web, 'index.html'), mode='w') as output_file:
            output_file.write(template.render({'repos_info': index_data}))


if __name__ == '__main__':
    publisher = OwlPub()
    publisher.run()
