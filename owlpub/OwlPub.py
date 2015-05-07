import json
import os
from RepoHandler import RepoHandler


class OwlPub:

    repos = {}

    def __init__(self):
        self.loadConfig()

    def loadConfig(self):
        with open("config.json") as config_file:
            config = json.load(config_file)
        directory_repos = os.path.abspath(config['directories']['repos'])
        directory_web = os.path.abspath(config['directories']['web'])
        for repo in config['repos']:
            repo_config = {}

            repo_config['name'] = repo['name']
            repo_config['clone_url'] = repo['clone_url']
            repo_config['repo_directory'] = os.path.join(directory_repos, os.path.splitext(os.path.basename(repo['clone_url']))[0])

            repo_config['web_directory'] = os.path.join(directory_web, repo_config['name'])

            if 'ontology_file' in repo:
                repo_config['ontology_file'] = os.path.join(repo_config['repo_directory'], repo['ontology_file'])
            else:
                repo_config['ontology_file'] = None

            if 'template_file' in repo:
                repo_config['template_file'] = os.path.join(
                    repo_config['repo_directory'], repo['template_file'])
            else:
                repo_config['template_file'] = None

            self.repos[repo['name']] = repo_config

    def getRepoConfigByCloneUrl(self, clone_url):
        for repo_name in self.repos:
            if self.repos[repo_name]['clone_url'] == clone_url:
                return self.getRepoConfig(repo_name)

    def getRepoConfig(self, repo_name):
        return self.repos[repo_name]

    def rise(self):
        for repo_name in self.repos:
            repo_handler = RepoHandler(self.getRepoConfig(repo_name))
            repo_handler.regenerate()
