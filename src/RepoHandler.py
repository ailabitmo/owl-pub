from os import makedirs
from os.path import realpath, join, dirname, exists, splitext, basename
from shutil import rmtree
from xml.sax._exceptions import SAXParseException

import requests
from git import Repo
from rdflib.exceptions import ParserError

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
        self.__check_branches()

    def __check_branches(self):
        branches = self.repo.branches
        branches.append('HEAD')
        branches.append('master')
        for i in self.repo.remote().refs:
            name = i.name.split('/')[1]
            if name not in branches:
                self.repo.create_head(name, i)

    def sync(self):
        self.__check_branches()
        self.repo.remotes['origin'].pull()

    @staticmethod
    def generate_ontology(_from, _to, branches_info, template):
        if not exists(branches_info['branch_dir']):
            makedirs(branches_info['branch_dir'])

        try:
            print(u'Parsing {0:s}...'.format(_from))

            generator = DocGenerator(_from)

            for export_format in ("owl", "ttl", "jsonld"):
                generator.export(join(branches_info['branch_dir'],
                                      _to + '.' + export_format),
                                 export_format)
            generator.generate_html_doc(
                join(branches_info['branch_dir'], _to + '.html'),
                branches_info,
                template)
        except (SAXParseException, ParserError):
            print(u'WARNING: Failed parsing {0:s}...'.format(_from))

    def __get_commits(self, ontology):
        # TODO: Make moar pretty
        if 'https://github.com/' in self.config['clone_url']:
            r = requests.get('https://api.github.com/repos/' +
                             # self.configs['clone_url'][19:].split('.')[0]
                             # or
                             # self.configs['clone_url'][19:-4]
                             # ?
                             self.config['clone_url'][19:].split('.')[0] +
                             '/commits?path=' +
                             ontology[len(self.config['directory']):])
            if r.status_code == 200:
                return r.json()
        else:
            # TODO: Get commits from git module directly
            pass
        return None

    def regenerate(self):
        # First, delete the previously generated files in webroot
        for ontology in self.config['ontologies']:
            if not exists(ontology['web_directory']):
                makedirs(ontology['web_directory'])
            else:
                rmtree(ontology['web_directory'])

        # Now generate_html_doc new files
        for ontology in self.config['ontologies']:
            if ontology['template'] is None or not exists(ontology['template']):
                template = join(dirname(realpath(__file__)),
                                'templates',
                                'default.html')
            else:
                template = ontology['template']

            all_branches = []
            # Generate branches & tags list for ontology
            for branch in (self.repo.branches + self.repo.tags):
                self.repo.git.execute(['git', 'checkout', branch.name])
                if exists(ontology['ontology']):
                    all_branches.append(branch.name)

            branches_info = {
                'commits': self.__get_commits(
                    ontology['ontology']
                )
            }

            for branch in (self.repo.branches + self.repo.tags):
                self.repo.git.execute(['git', 'checkout', branch.name])
                if exists(ontology['ontology']):
                    branches_info['current_branch'] = branch.name
                    branches_info['other_branches'] = [b for b in all_branches
                                                       if b not in branch.name]
                    branches_info['branch_dir'] = join(
                        ontology['web_directory'],
                        branch.name
                    )
                    branches_info['file_name'] = splitext(
                        basename(ontology['ontology'])
                    )[0]

                    self.generate_ontology(
                        ontology['ontology'],
                        branches_info['file_name'],
                        branches_info,
                        template
                    )

            self.repo.git.execute(['git', 'checkout', 'master'])
