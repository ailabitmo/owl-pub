import codecs
from rdflib import Graph, RDF, RDFS
from jinja2 import Template
import libs.OWL as OWL
import libs.DUBLINCORE as DC


class DocGenerator:

    def extract(self, ontology_path, preferred_language=u"en"):
        graph = Graph()
        graph.parse(ontology_path, format="xml")

        data = {}

        # ontology uri
        ontology_uri = graph[::OWL.Ontology].next()[0]
        data['ontology_uri'] = ontology_uri

        # ontology title
        for i in graph[ontology_uri:DC.title:]:
            data['ontology_title'] = i

        # creators (autors)
        data['creators'] = []
        for i in graph[ontology_uri:DC.creator:]:
            data['creators'].append(i)

        # contributors
        data['contributors'] = []
        for i in graph[ontology_uri:DC.contributor:]:
            data['contributors'].append(i)

        # date
        for i in graph[ontology_uri:DC.date:]:
            data['date'] = i

        # current version
        for i in graph[ontology_uri:OWL.versionInfo:]:
            data['current_version'] = i

        # imported ontologies
        data['imported_ontologies'] = []
        for i in graph[:OWL.imports:]:
            data['imported_ontologies'].append(i)

        # abstract
        for i in graph[ontology_uri:RDFS.comment:]:
            data['abstract'] = i

        # introduction
        for i in graph[ontology_uri:DC.description:]:
            data['introduction'] = i

        # classes
        data['classes'] = []

        classes = []
        for i in graph[:RDF.type:RDFS.Class]:
            classes.append(i)
        for i in graph[:RDF.type:OWL.Class]:
            classes.append(i)

        for i in classes:
            class_i = {}

            class_i['uri'] = i

            for x in graph[i:RDFS.label:]:
                if x.language == preferred_language or 'label' not in class_i:
                    class_i['label'] = x

            class_i['super_classes'] = []
            for x in graph[i:RDFS.subClassOf:]:
                class_i['super_classes'].append(x)

            class_i['sub_classes'] = []
            for x in graph[:RDFS.subClassOf:i]:
                class_i['sub_classes'].append(x)

            class_i['domain_for'] = []
            for x in graph[:RDFS.domain:i]:
                class_i['domain_for'].append(x)

            class_i['in_range'] = []
            for x in graph[:RDFS.range:i]:
                class_i['in_range'].append(x)

            data['classes'].append(class_i)

        # object properties

        data['object_properties'] = []

        object_properties = []
        for i in graph[::OWL.ObjectProperty]:
            object_properties.append(i)

        return data

    def render(self, data, template_path):
        template_file = open(template_path, "r")
        template = Template(template_file.read())
        return template.render(data)

    def generate(self, ontology_path, output_path, template_path, preferred_language=u'en'):

        data = self.extract(ontology_path, preferred_language)

        rendered = self.render(data, template_path)

        with codecs.open(output_path, encoding="utf-8", mode="w") as output:
            output.write(rendered)
