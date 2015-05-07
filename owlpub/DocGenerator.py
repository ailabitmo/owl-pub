from rdflib import Graph
import libs.OWL as OWL
import libs.DUBLINCORE as DC
from jinja2 import Template


class DocGenerator:

    ontology_path = None

    def __init__(self, ontology_path=None):
        self.ontology_path = ontology_path

    def extract(self, ontology_path=None, preferred_language=u"en"):
        data = {}

        graph = Graph()
        if self.ontology_path is not None:
            graph.parse(ontology_path, format="xml")
        else:
            graph.parse(self.ontology_path, format="xml")

        # ontology uri
        ontology_uri = graph[::OWL.Ontology].next()[0]
        data['ontology_uri'] = ontology_uri

        # ontology title
        for i in graph[ontology_uri:DC.title:]:
            data['ontology_title'] = i

        # extract any other data here, it's simply example

        return data

    def render(self, data, template_path=None):
        if template_path is not None:
            template_file = open(template_path, "r")
        else:
            template_file = open("template-default.html", "r")

        template = Template(template_file.read())
        return template.render(data)

    def generate(self, output_file, preferred_language=u'en', template_path=None):

        data = self.extract(self.ontology_path, preferred_language)

        rendered = self.render(data, template_path)

        with open(output_file, "w") as output:
            output.write(rendered)
