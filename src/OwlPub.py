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
    repos = []
    dir_web = None
    dir_repos = None
    template_index = None

    def __init__(self):
        self.load_config()

    def load_config(self):
        config_path = join(dirname(realpath(__file__)), 'config.json')

        with open(config_path) as config_file:
            config = json.load(config_file)

        try:
            self.dir_repos = abspath(config['directories']['repos'])
        except KeyError:
            self.dir_repos = abspath('repos')

        try:
            self.dir_web = abspath(config['directories']['web'])
        except KeyError:
            self.dir_web = abspath('webroot')

        self.template_index = config['template_index'] \
            if 'template_index' in config else None

        for repo in config['repos']:
            repo_config = self.parse_repo_config(repo)
            self.repos.append(repo_config)

        try:
            pass
        except:
            raise ParseConfigError(u'configs file invalid')

    def parse_repo_config(self, config):
        repo_name = splitext(basename(config['clone_url']))[0]
        dir_repo = join(self.dir_repos, repo_name)

        repo_config = {
            'directory': dir_repo,
            'clone_url': config['clone_url'],
            'webhook_id': config['webhook_id']
            if 'webhook_id' in config else None,
            'secret': config['secret'] if 'secret' in config else None,
            'ontologies': [self.parse_ontology_config(ontology, dir_repo)
                           for ontology in config['ontologies']]
        }

        return repo_config

    def parse_ontology_config(self, config, dir_repo):
        return {
            'ontology': join(dir_repo, config['ontology']),
            'template': join(dir_repo, config['template'])
            if 'template' in config else None,
            'web_directory': join(self.dir_web, config['directory'])
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
        # Data for index file
        index_data = []

        # Do some stuff with all repos
        for repo_config in self.repos:
            repo = RepoHandler(repo_config)
            repo.regenerate()

            # TODO: Make moar pretty
            index_data_ontologies = []
            for ontology in repo_config['ontologies']:
                name = ontology['web_directory'].replace(self.dir_web, '')[1:]
                path = name + '/master/' + \
                       splitext(basename(ontology['ontology']))[0] + '.html'
                if path.endswith('.git'):
                    path = path[:-4]
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
        if self.template_index is None or not exists(self.template_index):
            template_index_path = join(dirname(realpath(__file__)),
                                       'templates',
                                       'default-index.html')
        else:
            template_index_path = self.template_index

        env = Environment(trim_blocks=True, lstrip_blocks=True)
        with open(template_index_path, 'r') as template_index_file:
            template = env.from_string(template_index_file.read())
        with open(join(self.dir_web, 'index.html'), mode='w') as output_file:
            output_file.write(template.render({'repos_info': index_data}))


if __name__ == '__main__':
    publisher = OwlPub()
    publisher.rise()
