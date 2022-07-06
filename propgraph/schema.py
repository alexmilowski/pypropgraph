from lark import Lark

grammar = r"""
?schema: prolog? (_NEWLINE | node)*
prolog : LONG_STRING | STRING
node: "(" node_labels ("{" keys? "}")? ")" description? properties? relations?
node_labels: label+
keys: property_name ("," property_name)*
description: LONG_STRING | STRING
label: ":" NAME
properties: property+
property: "." property_name ("=" type? description?)?
type: NAME
relations: relation+
relation: "-" "[" relation_labels properties? "]" direction "(" target_nodes? ")" ("=" description?)?
relation_labels: label+
direction: UNDIRECTED | DIRECTED
target_nodes: target_node ("," target_node )*
target_node: label+
property_name: NAME | BACKQUOTE_STRING

BACKQUOTE_STRING: /`(?!'').*?(?<!\\)(\\\\)*?`/i
STRING: /'(?!'').*?(?<!\\)(\\\\)*?'/i
LONG_STRING: /('''.*?(?<!\\)(\\\\)*?''')/is
NAME: /[a-zA-Z_][\w\-]*/
COMMENT: /#[^\n]*/
_NEWLINE: ( /\r?\n[\t ]*/ | COMMENT )+
UNDIRECTED: "-"
DIRECTED.2: "->"
%ignore _NEWLINE
%ignore /[\t \f]+/  // WS


%import common.NEWLINE
%import common.WS_INLINE
%import common.LETTER
%import common.DIGIT

"""

class Schema:
   def __init__(self,description=''):
      self.description = description
      self.label_index = {}
      self.nodes = []

   def add_node(self,node):
      for label in node.labels:
         indexed = self.label_index.get(label,[])
         if len(indexed)==0:
            self.label_index[label] = indexed
         indexed.append(node)
      self.nodes.append(node)

   def find(self,*labels):
      if len(labels)==0:
         return []
      for label in labels:
         indexed = self.label_index.get(label)
         if indexed is not None:
            break
      if indexed is None:
         return []
      if len(labels)==1:
         return indexed
      label_set = set(labels)
      candidates = []
      for node in indexed:
         if node.labels.issubset(label_set):
            candidates.append(node)
      return candidates

   def documentation(self,output):

      print(self.description,file=output)
      print(file=output)

      for node in self.nodes:

         node.documentation(output)

class EdgeDefinition:

   default_datatype = 'string'

   def __init__(self,labels,directed=True,description=''):
      self.directed = directed
      self.description = description
      self.labels = set(labels)
      self.related = []
      self.properties = {}

   def add_related(self,labels):
      self.related.append(set(labels))

   def add_property(self,name,datatype=None,description=''):
      property = (name,datatype if datatype is not None else EdgeDefinition.default_datatype,description)
      self.properties[name] = property
      return property


class NodeDefinition:

   default_datatype = 'string'

   def __init__(self,description='',labels=[],keys=[]):
      self.description = description
      self.labels = set(labels)
      self.keys = set(keys)
      self.properties = {}
      self.relations = []

   def add_property(self,name,datatype=None,description=''):
      property = (name,datatype if datatype is not None else NodeDefinition.default_datatype,description)
      self.properties[name] = property
      return property

   def add_relation(self,labels,directed=True,description='',related=None):
      edge = EdgeDefinition(labels,directed,description)
      if related is not None:
         if isinstance(related,set):
            edge.add_related(related)
         elif type(related)!=isinstance(related,list):
            raise ValueError('{} is not a supported related label type'.format(str(type(related))))
         else:
            for related in map(lambda x : set(x),related):
               edge.add_related(related)
      self.relations.append(edge)
      return edge

   def documentation(self,output):

      print('# {}'.format(':'.join(self.labels)),file=output)
      if self.description is not None and len(self.description)>0:
         print(file=output)
         print(self.description,file=output)
      print(file=output)

      print('**Keys:** '+', '.join(map(lambda k: '*'+k+'*',self.keys)))
      print(file=output)

      if len(self.properties)>0:
         print('## Properties',file=output)
         print(file=output)

         print('<table>',file=output)
         print('<thead><tr><th>Property</th><th>Type</th><th>Description</th></tr></thead>',file=output)
         print('<tbody>',file=output)
         for name in sorted(self.properties.keys()):
            property_name, datatype, description = self.properties[name]
            print('<tr><td>{}</td><td>{}</td>'.format(property_name,datatype),end='',file=output)
            if description=='' or description is None:
               print('<td></td></tr>',file=output)
            else:
               print('<td>',file=output)
               print(file=output)
               print(description,file=output)
               print(file=output)
               print('</td></tr>',file=output)
         print('</tbody>',file=output)
         print('</table>',file=output)
         print(file=output)

      if len(self.relations)>0:
         print('## Relations',file=output)
         print(file=output)

         print('<table>',file=output)
         print('<thead><tr><th>Relation</th><th>Directed</th><th>Target</th></tr></thead>',file=output)
         print('<tbody>',file=output)

         for edge in self.relations:
            labels = ':'+':'.join(edge.labels)
            directed = 'yes'  if edge.directed else 'no'
            targets = '<br>'.join(list(map(lambda target: ':'+':'.join(target),edge.related)))
            rowspan = 0
            has_description = edge.description is not None and len(edge.description)>0
            if has_description:
               rowspan += 2
            if len(edge.properties)>0:
               rowspan += 1 + len(edge.properties) + sum(map(lambda property : 1 if property[2] is not None and len(property[2])>0 else 0,edge.properties.values()))

            print('<tr><td{}>{}</td><td>{}</td><td>{}</td></tr>'.format('' if rowspan==0 else ' rowspan={}'.format(str(rowspan)),labels,directed,targets),file=output)
            if has_description:
               print('<tr><td colspan=2>',file=output)
               print(file=output)
               print(edge.description,file=output)
               print(file=output)
               print('</td></tr>',file=output)

            if len(edge.properties)>0:
               print('<tr><th>Property</th><th>Type</th></tr>',file=output)
               for name in sorted(edge.properties.keys()):
                  property_name, datatype, description = edge.properties[name]
                  print('<tr><td>{}</td><td>{}</td></tr>'.format(property_name,datatype),file=output)
                  if description is not None and len(description)>0:
                     print('<tr><td colspan=2>',file=output)
                     print(file=output)
                     print(description,file=output)
                     print(file=output)
                     print('</td></tr>',file=output)


         print('</tbody>',file=output)
         print('</table>',file=output)
         print(file=output)


def _decode_literal(value):
   if value.startswith("'''"):
      return value[3:-3]
   else:
      return value[1:-1]

def _process_property(target,property):
   name = None
   datatype = None
   description = ''
   for facet in property.children:
      if facet.data=='property_name':
         name = facet.children[0].value
      elif facet.data=='type':
         datatype = facet.children[0].value
      elif facet.data=='description':
         description = _decode_literal(facet.children[0].value)
   target.add_property(name,datatype,description)

class SchemaParser:

   def __init__(self):
      self.parser = Lark(grammar,parser='lalr',start='schema')

   def parse(self,source):

      if type(source)!=str:
         source = source.read()

      tree = self.parser.parse(source)

      if tree.data=='schema':
         schema_description = _decode_literal(tree.children[0].children[0].value)
         schema = Schema(schema_description)
         schema_children = tree.children[1:]
      elif tree.data=='node':
         schema_description = ''
         schema = Schema(schema_description)
         schema_children = [tree]
      else:
         raise ValueError('Unhandled tree type: '+tree.data)

      for node in schema_children:

         node_description = ''
         labels = list(map(lambda label : label.children[0].value,node.children[0].children))
         keys = []


         last = 1
         for index,child in enumerate(node.children[1:]):
            last = index
            if child.data=='keys':
               keys = list(map(lambda label : label.children[0].value,child.children))
            elif child.data=='description':
               node_description = _decode_literal(child.children[0].value)
            else:
               break

         node_def = NodeDefinition(node_description,labels,keys)

         for child in node.children[index:]:
            if child.data=='properties':
               for property in child.children:
                  _process_property(node_def,property)
            elif child.data=='relations':
               for relation in child.children:
                  labels = list(map(lambda label : label.children[0].value,relation.children[0].children))
                  start = 2 if relation.children[1].data=='properties' else 1
                  directed = relation.children[start].children[0].value=='->'
                  edge = node_def.add_relation(labels,directed)
                  if relation.children[1].data=='properties': # properties to process
                     for property in relation.children[1].children:
                        _process_property(edge,property)
                  for facet in relation.children[start+1:]:
                     if facet.data=='target_nodes':
                        for target_node in facet.children:
                           edge.add_related(list(map(lambda label : label.children[0].value,target_node.children)))
                     elif facet.data=='description':
                        edge.description = _decode_literal(facet.children[0].value)


         schema.add_node(node_def)

      return schema

if __name__ == '__main__':
   import sys
   for file in sys.argv[1:]:
      parser = SchemaParser()
      with open(file,'r') as input:
         schema = parser.parse(input)
         schema.documentation(sys.stdout)
