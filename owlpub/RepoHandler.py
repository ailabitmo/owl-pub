from os.path import realpath, join, dirname, exists
from os import makedirs
from shutil import copy
from git import Repo
from DocGenerator import DocGenerator


class RepoHandler:

    repo = None
    config = None

    def __init__(self, config):
        try:
            repo = Repo(config['directory'])
        except:
            repo = Repo.clone_from(config['clone_url'], config['directory'])
        self.repo = repo
        self.config = config

    def sync(self):
        self.repo.remotes['origin'].pull()

    def regenerate(self):
        generator = DocGenerator()

        for i in self.config['ontologies']:
            if i['template'] is None:
                template_path = join(dirname(realpath(__file__)), "template.html")
            else:
                template_path = i['template']
            if not exists(dirname(i['web_doc'])):
                makedirs(dirname(i['web_doc']))
            generator.generate(i['ontology'], i['web_doc'], template_path)
            copy(i['ontology'], i['web_ontology'])
