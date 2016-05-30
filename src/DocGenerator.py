#!/usr/bin/python3 -B
# coding=utf-8

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
    _graph = None
    _ontology_iri = None
    _original_path = None
    _original_format = None
    _prefix = ''
    _base_namespace = ''

    def __init__(self, ontology_path):
        self._graph = Graph()
        self._graph.parse(ontology_path)

        for i in self._graph.namespaces():
            if i[0] == '':
                self._base_namespace = i[1]

        self._original_path = ontology_path
        self._original_format = splitext(basename(ontology_path))[1][1:]
        self._ontology_iri = next(self._graph[::OWL.Ontology])[0]

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

    @staticmethod
    def __hashed(value):
        return value if '/' in value else '#' + value

    def __prefixed(self, value):
        return value if '/' in value else self._prefix + value

    def __local_anchor_from_iri(self, full_iri):
        out = None
        if full_iri is not None and self._ontology_iri in full_iri:
            out = self.__anchor_from_iri(full_iri)
        return full_iri if out is None else out

    def __extract_text(self, subject=None, predicate=None, obj=None,
                       language='en'):
        out = None
        for i in self._graph[subject:predicate:obj]:
            if out is None or i.language == language:
                out = urlize(i).replace('\n', '<br />')
        return self.__local_anchor_from_iri(out)

    def __extract_array(self, subject=None, predicate=None, obj=None):
        return [self.__local_anchor_from_iri(i)
                for i in self._graph[subject:predicate:obj]]

    def __extract_bool(self, subject=None, predicate=None, obj=None):
        out = self.__extract_text(subject=subject, predicate=predicate, obj=obj)
        if out is not None and out.upper() == 'TRUE':
            return True
        return False

    def __extract_ontology_data(self, preferred_language='en'):
        data = {
            'ontology_iri': self._ontology_iri,
            'ontology_title':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=DC.title,
                                    language=preferred_language),
            'ontology_creators':
                self.__extract_array(subject=self._ontology_iri,
                                     predicate=DC.creator),
            'ontology_contributors':
                self.__extract_array(subject=self._ontology_iri,
                                     predicate=DC.contributor),
            'ontology_date':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=DC.date,
                                    language=preferred_language),
            'ontology_version':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=OWL.versionInfo,
                                    language=preferred_language),
            'ontology_version_iri':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=OWL.versionIRI,
                                    language=preferred_language),
            'imported_ontologies':
                self.__extract_array(subject=self._ontology_iri,
                                     predicate=OWL.imports),
            'abstract':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=RDFS.comment,
                                    language=preferred_language),
            'introduction':
                self.__extract_text(subject=self._ontology_iri,
                                    predicate=DC.description,
                                    language=preferred_language),
            'classes': [],
            'data_properties': [],
            'object_properties': [],
            'annotation_properties': [],
            'individuals': [],
        }

        # Classes
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri in self._graph[:RDF.type:RDFS.Class]
                          if iri.startswith(self._base_namespace)] + \
                         [iri for iri in self._graph[:RDF.type:OWL.Class]
                          if iri.startswith(self._base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                class_ = {
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

                if class_['label'] is None:
                    class_['label'] = 'None'

                if class_['is_deprecated']:
                    tmp_array_deprecated.append(class_)
                else:
                    tmp_array.append(class_)

        data['classes'] = \
            sorted(tmp_array, key=operator.itemgetter('label')) + \
            sorted(tmp_array_deprecated, key=operator.itemgetter('label'))

        # Data properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in self._graph[::OWL.DatatypeProperty]
                          if iri.startswith(self._base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                data_property = {
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

                if data_property['label'] is None:
                    data_property['label'] = 'None'

                if data_property['is_deprecated']:
                    tmp_array_deprecated.append(data_property)
                else:
                    tmp_array.append(data_property)

        data['data_properties'] = \
            sorted(tmp_array, key=operator.itemgetter('label')) + \
            sorted(tmp_array_deprecated, key=operator.itemgetter('label'))

        # Object properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in self._graph[::OWL.ObjectProperty]
                          if iri.startswith(self._base_namespace)]

        for iri in tmp_array_iris:
            object_property = {
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

            if object_property['label'] is None:
                for ii in self._graph[:RDFS.seeAlso:iri]:
                    object_property['label'] = \
                        self.__extract_text(subject=ii,
                                            predicate=RDFS.label,
                                            language=preferred_language)
            if object_property['label'] is None:
                object_property['label'] = 'None'

            if object_property['label'] is not None or \
                            object_property['comment'] is not None:
                if object_property['is_deprecated']:
                    tmp_array_deprecated.append(object_property)
                else:
                    tmp_array.append(object_property)

        data['object_properties'] = \
            sorted(tmp_array, key=operator.itemgetter('label')) + \
            sorted(tmp_array_deprecated, key=operator.itemgetter('label'))

        # Annotation properties
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []
        tmp_array_iris = [iri for iri, a in
                          self._graph[::OWL.AnnotationProperty]
                          if iri.startswith(self._base_namespace)]

        for iri in tmp_array_iris:
            if self.__extract_text(subject=iri,
                                   predicate=RDFS.label,
                                   language=preferred_language) is not None or \
                            self.__extract_text(subject=iri,
                                                predicate=RDFS.comment,
                                                language=preferred_language) \
                            is not None:
                annotation_property = {
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

                if annotation_property['label'] is None:
                    annotation_property['label'] = 'None'

                if annotation_property['is_deprecated']:
                    tmp_array_deprecated.append(annotation_property)
                else:
                    tmp_array.append(annotation_property)

        data['annotation_properties'] = \
            sorted(tmp_array, key=operator.itemgetter('label')) + \
            sorted(tmp_array_deprecated, key=operator.itemgetter('label'))

        # Individuals
        ########################################################################

        tmp_array = []
        tmp_array_deprecated = []

        tmp_array_iris = [iri for iri in self._graph.query('''
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

                if individual['label'] is None:
                    individual['label'] = 'None'

                if individual['is_deprecated']:
                    tmp_array_deprecated.append(individual)
                else:
                    tmp_array.append(individual)

        data['individuals'] = \
            sorted(tmp_array, key=operator.itemgetter('label')) + \
            sorted(tmp_array_deprecated, key=operator.itemgetter('label'))

        # Namespaces
        ########################################################################

        data['namespaces'] = []

        for k, v in self._graph.namespaces():
            if k == '':
                k = 'default'
            if self._ontology_iri in v and k != 'default':
                self._prefix = k + ':'
            data['namespaces'].append((k, v))

        # return
        ########################################################################

        return data

    def __render_doc(self, data, template_path):
        """ Render HTML documentation for the ontology """
        env = Environment(trim_blocks=True, lstrip_blocks=True)
        env.filters['md5filter'] = self.__md5_filter
        env.filters['anchorFromIRI'] = self.__anchor_from_iri
        env.filters['prefixed'] = self.__prefixed
        env.filters['hashed'] = self.__hashed
        with open(template_path, 'r') as template_file:
            template = env.from_string(template_file.read())
        return template.render(data)

    def generate_doc(self, output_path, branches_info, template_path,
                     preferred_language='en'):
        """ Generate HTML documentation for the ontology """
        data = self.__extract_ontology_data(preferred_language)
        data['branches_info'] = branches_info
        rendered = self.__render_doc(data, template_path)
        with codecs.open(output_path, encoding='utf-8', mode='w') \
                as output_file:
            output_file.write(rendered)

    def export(self, output_path, export_format):
        """ Export ontology to export_format from existing """
        if export_format == 'owl':
            if self._original_format == 'owl':
                copy(self._original_path, output_path)
            else:
                self._graph.serialize(output_path, 'pretty-xml')
        elif export_format == 'ttl':
            if self._original_format == 'ttl':
                copy(self._original_path, output_path)
            else:
                self._graph.serialize(output_path, 'turtle')
        elif export_format == 'jsonld':
            if self._original_format == 'jsonld':
                copy(self._original_path, output_path)
            else:
                self._graph.serialize(output_path, 'json-ld')
        else:
            raise ExportError('unexpected export format ' + str(export_format))
