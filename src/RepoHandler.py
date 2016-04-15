from os.path import realpath, join, dirname, exists, basename, splitext
from os import makedirs
from shutil import rmtree
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
        self.__checkBranches()

    def __checkBranches(self):
        branches = self.repo.branches
        branches.append('HEAD')
        branches.append('master')
        for i in self.repo.remote().refs:
            name = i.name.split('/')[1]
            if name not in branches:
                self.repo.create_head(name, i)

    def sync(self):
        self.__checkBranches()
        self.repo.remotes['origin'].pull()

    def regenerate(self):
        for conf_onto in self.config['ontologies']:

            if conf_onto['template'] is None or not exists(conf_onto['template']):
                template_path = join(dirname(realpath(__file__)), "template.html")
            else:
                template_path = conf_onto['template']

            base_name = splitext(basename(conf_onto['ontology']))[0]

            if not exists(conf_onto['web_directory']):
                makedirs(conf_onto['web_directory'])
            else:
                rmtree(conf_onto['web_directory'])

            for branch in self.repo.branches:
                branch.checkout()
                branch_directory = join(conf_onto['web_directory'], branch.name)
                if not exists(branch_directory):
                    makedirs(branch_directory)

                if exists(conf_onto['ontology']):
                    generator = DocGenerator(conf_onto['ontology'])

                    for export_format in conf_onto['export_formats']:
                        generator.export(join(branch_directory, base_name + '.' + export_format), export_format)

                    generator.generate(join(branch_directory, base_name + '.html'), template_path)
