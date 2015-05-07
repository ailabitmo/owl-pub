import os
import shutil
from DocGenerator import DocGenerator
from git import Repo, InvalidGitRepositoryError


class RepoHandler:

    repo = None
    config = None

    def __init__(self, repo_config):
        if self.check(repo_config):
            self.repo = Repo(repo_config['repo_directory'])
        else:
            self.repo = self.clone(repo_config)
        self.config = repo_config

    def check(self, repo_config):
        if not os.path.isdir(repo_config['repo_directory']):
            return False
        try:
            Repo(repo_config['repo_directory'])
        except InvalidGitRepositoryError:
            return False
        return True

    def clone(self, repo_config):
        return Repo.clone_from(repo_config['clone_url'], repo_config['repo_directory'])

    def pull(self):
        self.repo.remotes['origin'].pull()

    def regenerate(self):
        if self.config['ontology_file'] is None:
            for file in os.listdir(self.config['repo_directory']):
                if file.endswith(".owl"):
                    self.config['ontology_file'] = os.path.join(self.config['repo_directory'], file)

        doc = DocGenerator(self.config['ontology_file'])

        if not os.path.isdir(self.config['web_directory']):
            os.makedirs(self.config['web_directory'])

        output_file = os.path.join(self.config['web_directory'], os.path.splitext(os.path.basename(self.config['ontology_file']))[0] + '.html')
        doc.generate(template_path=self.config['template_file'], output_file=output_file)
        shutil.copy(self.config['ontology_file'], os.path.join(self.config['web_directory'], os.path.basename(self.config['ontology_file'])))
