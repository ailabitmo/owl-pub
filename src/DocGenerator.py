import codecs
import operator
from hashlib import md5
from os.path import splitext, basename
from shutil import copy

from jinja2 import Environment
from jinja2.utils import urlize
from rdflib import Graph, RDF, RDFS, OWL
from rdflib.namespace import DC
from rdflib.term import URIRef
from rfc3987 import parse


class ExportError(Exception):
    def __init__(self, arg):
        super(ExportError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class DocGenerator:
    graph = None
    ontology_iri = None
    original_path = None
    original_format = None
    base_namespace = ''

    def __init__(self, ontology_path):
        self.graph = Graph()
        self.graph.parse(ontology_path)

        for i in self.graph.namespaces():
            if i[0] == '':
                self.base_namespace = i[1]

        self.original_path = ontology_path
        self.original_format = splitext(basename(ontology_path))[1][1:]
        self.ontology_iri = self.graph[::OWL.Ontology].next()[0]

    @staticmethod
    def __md5_filter(value):
        return md5(value).hexdigest()

    @staticmethod
    def __anchor_from_iri(value):
        try:
            if parse(value, rule='IRI'):
                return value.split('#')[1]
        except (ValueError, IndexError):
            pass
        return None

    def __local_anchor_from_iri(self, full_iri):
        out = None
        if full_iri is not None and self.ontology_iri in full_iri:
            out = self.__anchor_from_iri(full_iri)
        return full_iri if out is None else '#' + out

    def __extract_text(self, subject=None, predicate=None, obj=None,
                       language=u'en'):
        out = None
        for i in self.graph[subject:predicate:obj]:
            if out is None or i.language == language:
                out = urlize(i).replace('\n', '<br />')
        return self.__local_anchor_from_iri(out)

    def __extract_array(self, subject=None, predicate=None, obj=None):
        return [self.__local_anchor_from_iri(i)
                for i in self.graph[subject:predicate:obj]]

    def __extract_bool(self, subject=None, predicate=None, obj=None):
        out = self.__extract_text(subject=subject,
                                  predicate=predicate,
                                  obj=obj)
        if out is not None and out.upper() == 'TRUE':
            return True
        return False

    def extract(self, branches_info, preferred_language=u'en'):
        data = {
            'ontology_iri': self.ontology_iri,
            'ontology_title':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=DC.title,
                                    language=preferred_language),
            'ontology_creators':
                self.__extract_array(subject=self.ontology_iri,
                                     predicate=DC.creator),
            'ontology_contributors':
                self.__extract_array(
                    subject=self.ontology_iri, predicate=DC.contributor),
            'ontology_date':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=DC.date,
                                    language=preferred_language),
            'ontology_version':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=OWL.versionInfo,
                                    language=preferred_language),
            'ontology_version_iri':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=OWL.versionIRI,
                                    language=preferred_language),
            'imported_ontologies':
                self.__extract_array(subject=self.ontology_iri,
                                     predicate=OWL.imports),
            'abstract':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=RDFS.comment,
                                    language=preferred_language),
            'introduction':
                self.__extract_text(subject=self.ontology_iri,
                                    predicate=DC.description,
                                    language=preferred_language),
            'classes': [],
            'data_properties': [],
            'object_properties': [],
            'annotation_properties': [],
            'individuals': [],
            'branches_info': branches_info
        }

        # Classes
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri in self.graph[:RDF.type:RDFS.Class]
                          if iri.startswith(self.base_namespace)] + \
                         [iri for iri in self.graph[:RDF.type:OWL.Class]
                          if iri.startswith(self.base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                cls = {
                    'iri': iri,
                    'label':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.label,
                                            language=preferred_language),
                    'comment':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.comment,
                                            language=preferred_language),
                    'super_classes':
                        sorted(self.__extract_array(subject=iri,
                                                    predicate=RDFS.subClassOf)),
                    'sub_classes':
                        sorted(self.__extract_array(predicate=RDFS.subClassOf,
                                                    obj=iri)),
                    'domain_for':
                        sorted(self.__extract_array(predicate=RDFS.domain,
                                                    obj=iri)),
                    'in_range':
                        sorted(self.__extract_array(predicate=RDFS.range,
                                                    obj=iri)),
                    'is_deprecated':
                        self.__extract_bool(subject=iri,
                                            predicate=OWL.deprecated)
                }

                if cls['is_deprecated']:
                    tmp_array_deprecated.append(cls)
                else:
                    tmp_array.append(cls)

        data['classes'] = sorted(tmp_array,
                                 key=operator.itemgetter('label')) + \
                          sorted(tmp_array_deprecated,
                                 key=operator.itemgetter('label'))

        # Data properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in self.graph[::OWL.DatatypeProperty]
                          if iri.startswith(self.base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                dprop = {
                    'iri': iri,
                    'label':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.label,
                                            language=preferred_language),
                    'comment':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.comment,
                                            language=preferred_language),
                    'super_properties':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.subPropertyOf),
                    'sub_properties':
                        self.__extract_array(predicate=RDFS.subPropertyOf,
                                             obj=iri),
                    'domain_for':
                        self.__extract_array(predicate=RDFS.domain,
                                             obj=iri),
                    'has_domain':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.domain),
                    'in_range':
                        self.__extract_array(predicate=RDFS.range,
                                             obj=iri),
                    'has_range':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.range),
                    'is_deprecated':
                        self.__extract_bool(subject=iri,
                                            predicate=OWL.deprecated)
                }

                # print type(dprop['has_domain'][0])

                if dprop['is_deprecated']:
                    tmp_array_deprecated.append(dprop)
                else:
                    tmp_array.append(dprop)

        data['data_properties'] = sorted(tmp_array,
                                         key=operator.itemgetter('label')) + \
                                  sorted(tmp_array_deprecated,
                                         key=operator.itemgetter('label'))

        # Object properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in self.graph[::OWL.ObjectProperty]
                          if iri.startswith(self.base_namespace)]

        for iri in tmp_array_iris:
            oprop = {
                'iri': iri,
                'label': self.__extract_text(subject=iri,
                                             predicate=RDFS.label,
                                             language=preferred_language),
                'comment':
                    self.__extract_text(subject=iri,
                                        predicate=RDFS.comment,
                                        language=preferred_language),
                'super_properties':
                    self.__extract_array(subject=iri,
                                         predicate=RDFS.subPropertyOf),
                'sub_properties':
                    self.__extract_array(predicate=RDFS.subPropertyOf,
                                         obj=iri),
                'domain_for':
                    self.__extract_array(predicate=RDFS.domain,
                                         obj=iri),
                'has_domain':
                    self.__extract_array(subject=iri,
                                         predicate=RDFS.domain),
                'in_range':
                    self.__extract_array(predicate=RDFS.range,
                                         obj=iri),
                'has_range':
                    self.__extract_array(subject=iri,
                                         predicate=RDFS.range),
                'is_deprecated':
                    self.__extract_bool(subject=iri,
                                        predicate=OWL.deprecated)
            }

            if oprop['label'] is None:
                for ii in self.graph[:RDFS.seeAlso:iri]:
                    oprop['label'] = \
                        self.__extract_text(subject=ii,
                                            predicate=RDFS.label,
                                            language=preferred_language)

            if oprop['label'] is not None or oprop['comment'] is not None:
                if oprop['is_deprecated']:
                    tmp_array_deprecated.append(oprop)
                else:
                    tmp_array.append(oprop)

        data['object_properties'] = sorted(tmp_array,
                                           key=operator.itemgetter('label')) + \
                                    sorted(tmp_array_deprecated,
                                           key=operator.itemgetter('label'))

        # Annotation properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in self.graph[::OWL.AnnotationProperty]
                          if iri.startswith(self.base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                aprop = {
                    'iri': iri,
                    'label':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.label,
                                            language=preferred_language),
                    'comment':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.comment,
                                            language=preferred_language),
                    'super_properties':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.subPropertyOf),
                    'sub_properties':
                        self.__extract_array(predicate=RDFS.subPropertyOf,
                                             obj=iri),
                    'domain_for':
                        self.__extract_array(predicate=RDFS.domain,
                                             obj=iri),
                    'has_domain':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.domain),
                    'in_range':
                        self.__extract_array(predicate=RDFS.range,
                                             obj=iri),
                    'has_range':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.range),
                    'is_deprecated':
                        self.__extract_bool(subject=iri,
                                            predicate=OWL.deprecated)
                }

                if aprop['is_deprecated']:
                    tmp_array_deprecated.append(aprop)
                else:
                    tmp_array.append(aprop)

        data['annotation_properties'] = sorted(tmp_array,
                                               key=operator.itemgetter(
                                                   'label')) + \
                                        sorted(tmp_array_deprecated,
                                               key=operator.itemgetter('label'))

        # Individuals
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []

        # tmp_array_iris = [iri for iri, a in self.graph[::OWL.NamedIndividual]
        #                   if iri.startswith(self.base_namespace)]
        # print len(tmp_array_iris)

        # tmp_array_iris = [iri for iri in
        #                   self.graph.query(
        #                       'SELECT ?i ?c WHERE {?i rdf:type ?c} ')]
        # print len(tmp_array_iris)

        tmp_array_iris = [iri for iri in
                          self.graph.query('''
SELECT ?i WHERE {?i rdf:type ?c . ?c rdf:type <http://www.w3.org/2002/07/owl#Class> . }
''')]

        for iri in tmp_array_iris:
            iri = iri[0]
            if type(iri) is URIRef:
                individual = {
                    'iri': iri,
                    'label':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.label,
                                            language=preferred_language),
                    'comment':
                        self.__extract_text(subject=iri,
                                            predicate=RDFS.comment,
                                            language=preferred_language),
                    'super_properties':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.subPropertyOf),
                    'sub_properties':
                        self.__extract_array(predicate=RDFS.subPropertyOf,
                                             obj=iri),
                    'domain_for':
                        self.__extract_array(predicate=RDFS.domain,
                                             obj=iri),
                    'has_domain':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.domain),
                    'in_range':
                        self.__extract_array(predicate=RDFS.range,
                                             obj=iri),
                    'has_range':
                        self.__extract_array(subject=iri,
                                             predicate=RDFS.range),
                    'type': None,
                    'is_deprecated':
                        self.__extract_bool(subject=iri,
                                            predicate=OWL.deprecated)
                }

                if individual['is_deprecated']:
                    tmp_array_deprecated.append(individual)
                else:
                    tmp_array.append(individual)

        data['individuals'] = sorted(tmp_array,
                                     key=operator.itemgetter('label')) + \
                              sorted(tmp_array_deprecated,
                                     key=operator.itemgetter('label'))

        # Namespaces
        ########################################################################

        data['namespaces'] = []

        for k, v in self.graph.namespaces():
            if k == '':
                k = 'default'
            data['namespaces'].append((k, v))

        # return
        ########################################################################

        return data

    def render(self, data, template_path):
        """ Render HTML documentation for the ontology """
        template_file = open(template_path, 'r')
        env = Environment(trim_blocks=True, lstrip_blocks=True)
        env.filters['md5filter'] = self.__md5_filter
        env.filters['anchorFromIRI'] = self.__anchor_from_iri
        template = env.from_string(template_file.read())
        return template.render(data)

    def generate(self, output_path, branches_info, template_path,
                 preferred_language=u'en'):
        """ Generate HTML documentation for the ontology """
        data = self.extract(branches_info, preferred_language)
        rendered = self.render(data, template_path)
        with codecs.open(output_path, encoding='utf-8', mode='w') as output:
            output.write(rendered)

    def export(self, output_path, export_format):
        """ Export ontology to export_format from existing """
        if export_format == 'owl':
            if self.original_format == 'owl':
                copy(self.original_path, output_path)
            else:
                self.graph.serialize(output_path, 'pretty-xml')
        elif export_format == 'ttl':
            if self.original_format == 'ttl':
                copy(self.original_path, output_path)
            else:
                self.graph.serialize(output_path, 'turtle')
        elif export_format == 'jsonld':
            if self.original_format == 'jsonld':
                copy(self.original_path, output_path)
            else:
                self.graph.serialize(output_path, 'json-ld')
        else:
            raise ExportError('unexpected export format ' + str(export_format))
