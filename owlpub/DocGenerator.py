import codecs
from os.path import splitext, basename
from shutil import copy
from rdflib import Graph, RDF, RDFS, OWL
from rdflib.namespace import DC
from jinja2 import Environment
from hashlib import md5


class ExportError(Exception):
    def __init__(self, arg):
        super(ExportError, self).__init__()
        self.arg = arg

    def __str__(self):
        return str(self.arg)


class DocGenerator:

    original_path = None
    original_format = None
    graph = None
    base_namespace = None

    def __init__(self, ontology_path):
        self.graph = Graph()
        self.graph.parse(ontology_path)

        for i in self.graph.namespaces():
            if i[0] == '':
                self.base_namespace = i[1]

        self.original_path = ontology_path
        self.original_format = splitext(basename(ontology_path))[1][1:]

    def __md5filter(self, value):
        return md5(value).hexdigest()

    def __anchorFromIRI(self, value):
        return value.split('#')[1]

    def __extractText(self, subject=None, predicate=None, obj=None, language=u"en"):
        out = None
        for i in self.graph[subject:predicate:obj]:
            if out is None or i.language == language:
                out = i
        return out

    def __extractArray(self, subject=None, predicate=None, obj=None):
        out = []
        for i in self.graph[subject:predicate:obj]:
            out.append(i)
        return out

    def extract(self, preferred_language=u"en"):

        data = {}

        # ontology uri
        ontology_iri = self.graph[::OWL.Ontology].next()[0]
        data['ontology_iri'] = ontology_iri

        data['ontology_title'] = self.__extractText(subject=ontology_iri, predicate=DC.title, language=preferred_language)

        data['ontology_creators'] = self.__extractArray(subject=ontology_iri, predicate=DC.creator)

        data['ontology_contributors'] = self.__extractArray(subject=ontology_iri, predicate=DC.contributor)

        data['ontology_date'] = self.__extractText(subject=ontology_iri, predicate=DC.date, language=preferred_language)

        data['ontology_version'] = self.__extractText(subject=ontology_iri, predicate=OWL.versionInfo, language=preferred_language)

        data['ontology_version_iri'] = self.__extractText(subject=ontology_iri, predicate=OWL.versionIRI, language=preferred_language)

        data['imported_ontologies'] = self.__extractArray(subject=ontology_iri, predicate=OWL.imports)

        data['abstract'] = self.__extractText(subject=ontology_iri, predicate=RDFS.comment, language=preferred_language)

        data['introduction'] = self.__extractText(subject=ontology_iri, predicate=DC.description, language=preferred_language)

        # classes
        data['classes'] = []

        classes = []
        for i in self.graph[:RDF.type:RDFS.Class]:
            if i.startswith(self.base_namespace):
                classes.append(i)
        for i in self.graph[:RDF.type:OWL.Class]:
            if i.startswith(self.base_namespace):
                classes.append(i)

        for i in classes:
            class_i = {}

            class_i['iri'] = i

            class_i['label'] = self.__extractText(subject=i, predicate=RDFS.label, language=preferred_language)

            class_i['comment'] = self.__extractText(subject=i, predicate=RDFS.comment, language=preferred_language)

            class_i['super_classes'] = self.__extractArray(subject=i, predicate=RDFS.subClassOf)

            class_i['sub_classes'] = self.__extractArray(predicate=RDFS.subClassOf, obj=i)

            class_i['domain_for'] = self.__extractArray(predicate=RDFS.domain, obj=i)

            class_i['in_range'] = self.__extractArray(predicate=RDFS.range, obj=i)

            data['classes'].append(class_i)

        # object properties

        data['object_properties'] = []

        object_properties = []
        for i, a in self.graph[::OWL.ObjectProperty]:
            if i.startswith(self.base_namespace):
                object_properties.append(i)

        for i in object_properties:
            object_property_i = {}

            object_property_i['iri'] = i

            object_property_i['label'] = self.__extractText(subject=i, predicate=RDFS.label, language=preferred_language)
            if object_property_i['label'] is None:
                for ii in self.graph[:RDFS.seeAlso:i]:
                    object_property_i['label'] = self.__extractText(subject=ii, predicate=RDFS.label, language=preferred_language)

            object_property_i['comment'] = self.__extractText(subject=i, predicate=RDFS.comment, language=preferred_language)

            object_property_i['super_properties'] = self.__extractArray(subject=i, predicate=RDFS.subPropertyOf)

            object_property_i['sub_properties'] = self.__extractArray(predicate=RDFS.subPropertyOf, obj=i)

            object_property_i['domain_for'] = self.__extractArray(predicate=RDFS.domain, obj=i)

            object_property_i['has_domain'] = self.__extractArray(subject=i, predicate=RDFS.domain)

            object_property_i['in_range'] = self.__extractArray(predicate=RDFS.range, obj=i)

            object_property_i['has_range'] = self.__extractArray(subject=i, predicate=RDFS.range)

            data['object_properties'].append(object_property_i)

        # data properties

        data['data_properties'] = []

        data_properties = []
        for i, a in self.graph[::OWL.DatatypeProperty]:
            if i.startswith(self.base_namespace):
                data_properties.append(i)

        for i in data_properties:
            data_property_i = {}

            data_property_i['iri'] = i

            data_property_i['label'] = self.__extractText(subject=i, predicate=RDFS.label, language=preferred_language)

            data_property_i['comment'] = self.__extractText(subject=i, predicate=RDFS.comment, language=preferred_language)

            data_property_i['super_properties'] = self.__extractArray(subject=i, predicate=RDFS.subPropertyOf)

            data_property_i['sub_properties'] = self.__extractArray(predicate=RDFS.subPropertyOf, obj=i)

            data_property_i['domain_for'] = self.__extractArray(predicate=RDFS.domain, obj=i)

            data_property_i['has_domain'] = self.__extractArray(subject=i, predicate=RDFS.domain)

            data_property_i['in_range'] = self.__extractArray(predicate=RDFS.range, obj=i)

            data_property_i['has_range'] = self.__extractArray(subject=i, predicate=RDFS.range)

            data['data_properties'].append(data_property_i)

        # annotation properties

        data['annotation_properties'] = []

        annotation_properties = []
        for i, a in self.graph[::OWL.AnnotationProperty]:
            if i.startswith(self.base_namespace):
                annotation_properties.append(i)

        for i in annotation_properties:
            annotation_property_i = {}

            annotation_property_i['iri'] = i

            annotation_property_i['label'] = self.__extractText(subject=i, predicate=RDFS.label, language=preferred_language)

            annotation_property_i['comment'] = self.__extractText(subject=i, predicate=RDFS.comment, language=preferred_language)

            annotation_property_i['super_properties'] = self.__extractArray(subject=i, predicate=RDFS.subPropertyOf)

            annotation_property_i['sub_properties'] = self.__extractArray(predicate=RDFS.subPropertyOf, obj=i)

            annotation_property_i['domain_for'] = self.__extractArray(predicate=RDFS.domain, obj=i)

            annotation_property_i['has_domain'] = self.__extractArray(subject=i, predicate=RDFS.domain)

            annotation_property_i['in_range'] = self.__extractArray(predicate=RDFS.range, obj=i)

            annotation_property_i['has_range'] = self.__extractArray(subject=i, predicate=RDFS.range)

            data['data_properties'].append(annotation_property_i)

        # namespaces

        data['namespaces'] = []

        for k, v in self.graph.namespaces():
            if k == '':
                k = 'default'
            data['namespaces'].append((k, v))

        return data

    def render(self, data, template_path):
        template_file = open(template_path, "r")
        env = Environment()
        env.filters['md5filter'] = self.__md5filter
        env.filters['anchorFromIRI'] = self.__anchorFromIRI
        template = env.from_string(template_file.read())
        return template.render(data)

    def generate(self, output_path, template_path, preferred_language=u'en'):

        data = self.extract(preferred_language)

        rendered = self.render(data, template_path)

        with codecs.open(output_path, encoding="utf-8", mode="w") as output:
            output.write(rendered)

    def export(self, output_path, export_format):
        if export_format == 'owl':
            if(self.original_format == 'owl'):
                copy(self.original_path, output_path)
            else:
                self.graph.serialize(output_path, "pretty-xml")
        elif export_format == 'ttl':
            if(self.original_format == 'ttl'):
                copy(self.original_path, output_path)
            else:
                self.graph.serialize(output_path, "turtle")
        else:
            raise ExportError('unexcepted export format "' + str(export_format) + '"')
