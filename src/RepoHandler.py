from os import makedirs
from os.path import realpath, join, dirname, exists, splitext, basename
from shutil import rmtree
from xml.sax._exceptions import SAXParseException

import requests
from git import Repo
from rdflib.exceptions import ParserError

from DocGenerator import DocGenerator


class RepoHandler:
    _repo = None
    _config = None

    def __init__(self, config):
        try:
            self._repo = Repo(config['directory'])
        except:
            self._repo = Repo.clone_from(config['clone_url'],
                                         config['directory'])

        print(u'Repo {0:s}'.format(config['clone_url']))

        self._config = config
        self.sync()

    def __check_branches(self):
        branches = self._repo.branches
        branches.append('HEAD')
        branches.append('master')
        for i in self._repo.remote().refs:
            name = i.name.split('/')[1]
            if name not in branches:
                self._repo.create_head(name, i)

    def sync(self):
        self.__check_branches()
        self._repo.remotes['origin'].pull()

    @staticmethod
    def __generate_ontology(from_, to_, branches_info, template):
        if not exists(branches_info['branch_dir']):
            makedirs(branches_info['branch_dir'])

        try:
            print(u'Parsing {0:s}'.format(from_))

            generator = DocGenerator(from_)

            for export_format in ("owl", "ttl", "jsonld"):
                generator.export(
                    join(branches_info['branch_dir'],
                         to_ + '.' + export_format),
                    export_format
                )
            generator.generate_doc(
                join(branches_info['branch_dir'], to_ + '.html'),
                branches_info,
                template
            )
        except (SAXParseException, ParserError):
            print(u'WARNING: Failed parsing {0:s}...'.format(from_))

    def __get_commits(self, ontology):
        # TODO: Make moar pretty
        if 'https://github.com/' in self._config['clone_url']:
            r = requests.get('https://api.github.com/repos/' +
                             self._config['clone_url'][19:-4] +
                             '/commits?path=' +
                             ontology[len(self._config['directory']):])
            if r.status_code == 200:
                return r.json()
        else:
            # TODO: Get commits from git module directly
            pass
        return None

    def regenerate(self):
        # First, delete the previously generated files in webroot
        for ontology in self._config['ontologies']:
            if not exists(ontology['webname_dir']):
                makedirs(ontology['webname_dir'])
            else:
                rmtree(ontology['webname_dir'])

        # Now generate new files
        for ontology in self._config['ontologies']:
            if ontology['template'] is None or not exists(ontology['template']):
                template = join(
                    dirname(realpath(__file__)), 'templates', 'default.html'
                )
            else:
                template = ontology['template']

            # Generate branches & tags list for ontology
            all_branches = []
            for branch in (self._repo.branches + self._repo.tags):
                self._repo.git.execute(['git', 'checkout', branch.name])
                if exists(ontology['ontology']):
                    all_branches.append(branch.name)

            branches_info = {
                'commits': self.__get_commits(
                    ontology['ontology']
                )
            }

            # Generate documentation
            for branch in all_branches:
                self._repo.git.execute(['git', 'checkout', branch])

                branches_info['current_branch'] = branch
                branches_info['other_branches'] = [b for b in all_branches
                                                   if b != branch]
                branches_info['branch_dir'] = join(
                    ontology['webname_dir'], branch
                )
                branches_info['file_name'] = splitext(
                    basename(ontology['ontology'])
                )[0]

                self.__generate_ontology(
                    ontology['ontology'],
                    branches_info['file_name'],
                    branches_info,
                    template
                )

        self._repo.git.execute(['git', 'checkout', 'master'])
