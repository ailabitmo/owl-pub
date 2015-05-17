import json
from RepoHandler import RepoHandler
from os.path import abspath, join, splitext, basename, realpath, dirname


class ParseConfigError(Exception):
    """docstring for ParseConfigError"""
    def __init__(self, arg):
        super(ParseConfigError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class RepositoryNotFoundError(Exception):
    """docstring for RepositoryNotFoundError"""
    def __init__(self, arg):
        super(RepositoryNotFoundError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class OwlPub:

    repos = []

    def __init__(self):
        self.loadConfig()

    def loadConfig(self):
        try:
            config_path = join(dirname(realpath(__file__)), 'config.json')
            with open(config_path) as config_file:
                config = json.load(config_file)
            dir_repos = abspath(config['directories']['repos'])
            dir_web = abspath(config['directories']['web'])
            for i in config['repos']:
                repo_config = self.parseRepoConfig(i, dir_repos, dir_web)
                self.repos.append(repo_config)
        except:
            raise ParseConfigError(u"config file invalid")

    def parseRepoConfig(self, config, dir_repos, dir_web):
        repo_name = splitext(basename(config['clone_url']))[0]
        dir_repo = join(dir_repos, repo_name)

        repo_config = {}

        repo_config['directory'] = dir_repo

        repo_config['clone_url'] = config['clone_url']

        repo_config['webhook_id'] = None
        if 'webhook_id' in config:
            repo_config['webhook_id'] = config['webhook_id']

        if 'secret' in config:
            repo_config['secret'] = config['secret']

        repo_config['ontologies'] = []
        for i in config['ontologies']:
            ontology_config = self.parseOntologyConfig(i, dir_repo, dir_web)
            repo_config['ontologies'].append(ontology_config)

        return repo_config

    def parseOntologyConfig(self, config, dir_repo, dir_web):
        current_webdir = join(dir_web, config['webname'])
        ontology_name = splitext(basename(config['file']))[0] + ".owl"
        doc_name = splitext(basename(config['file']))[0] + ".html"

        ontology_config = {}

        ontology_config['ontology'] = join(dir_repo, config['file'])

        ontology_config['template'] = None
        if 'template' in config:
            ontology_config['template'] = join(dir_repo, config['template'])

        ontology_config['web_ontology'] = join(current_webdir, ontology_name)

        ontology_config['web_doc'] = join(current_webdir, doc_name)

        return ontology_config

    def getRepoByWebhookId(self, webhook_id):
        for repo_config in self.repos:
            if repo_config['webhook_id'] == webhook_id:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError(u"repository with webhook_id " + str(webhook_id) + u" not found!")

    def getRepoByCloneUrl(self, clone_url):
        for repo_config in self.repos:
            if repo_config['clone_url'] == clone_url:
                return RepoHandler(repo_config)
        raise RepositoryNotFoundError(u"repository with clone_url " + str(clone_url) + u" not found!")

    def rise(self):
        for repo_config in self.repos:
            repo = RepoHandler(repo_config)
            repo.regenerate()

if __name__ == "__main__":
    publisher = OwlPub()
    publisher.rise()
