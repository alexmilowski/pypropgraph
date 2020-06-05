import yaml
import csv
from io import StringIO
import os

from .schema import SchemaParser

from typing import NamedTuple, Generator, Iterator

class NodeItem(NamedTuple):
   labels: set
   keys: set
   properties: dict

class EdgeRelationItem(NamedTuple):
   labels: set
   from_labels: set
   from_node: dict
   to_labels: set
   to_node: dict
   directed: bool
   properties: dict

def cypher_literal(value):
   return "'" + value.replace('\\','\\\\').replace("'",r"\'") + "'"

def _label_list(spec):
   labels = spec.get('~label')
   if labels is None:
      labels = set()
   if type(labels)!=list:
      labels = set([labels])
   return set(labels)

def _get_id_properties(schema,labels):
   node_def = None
   if schema is not None:
      node_defs = schema.find(*labels)
      node_def = node_defs[0] if len(node_defs)>0 else None

   return node_def.keys if node_def is not None else set()

def _get_property(propdef):
   name = propdef.get('name')
   if name is None:
      raise ValueError("Missing the 'name' key for a property")
   value = propdef.get('value')
   if value is None:
      raise ValueError("Missing the 'value' key for a property")
   return (name,value)

def _node_properties(node):
   keys = set()
   for name in node.keys():
      if name[0]=='~':
         continue
      keys.add(name)
   return keys

def _create_edge(source, schema, from_id, to_id, directed, edge_labels, edge):
   from_node = source.get(from_id)
   if from_node is None:
      raise ValueError('Cannot find source node with id {}, edge {}'.format(from_id,':'.join(edge_labels)))
   to_node = source.get(to_id)
   if to_node is None:
      raise ValueError('Cannot find target node with id {}, edge {}'.format(to_id,':'.join(edge_labels)))
   from_to_id = []
   for label, id, node in [('from',from_id,from_node),('to',to_id,to_node)]:
      labels = _label_list(node)
      id_properties = _get_id_properties(schema,labels)
      if id_properties is None or len(id_properties)==0:
         id_properties = _node_properties(node)

      from_to_id.append((labels,list(map(lambda name: (name,node.get(name)),id_properties))))

   edge_item = EdgeRelationItem(edge_labels,from_to_id[0][0],dict(from_to_id[0][1]),from_to_id[1][0],dict(from_to_id[1][1]),directed,{})
   for key in edge.keys():
      if key[0]=='~':
         continue
      value = edge.get(key)
      edge_item.properties[key] = value

   return edge_item

def cypher_for_edge_relation(relation,merge=True):
   q = StringIO()
   for label, labels, id_properties in [('from',relation.from_labels,relation.from_node),('to',relation.to_labels,relation.to_node)]:
      q.write('MERGE ({label}{labels}'.format(label=label,labels=':' + ':'.join(labels) if len(labels)>0 else ''))
      q.write(' {')
      for index,id_property in enumerate(id_properties.keys()):
         if index>0:
            q.write(', ')
         value = id_properties.get(id_property)
         if value is None:
            raise ValueError('Node does not have id property {property} value'.format(property=id_property))
         if type(value)==str:
            value = cypher_literal(value)
         q.write('{property}: {value}'.format(property=id_property,value=value))
      q.write('})\n')
   if relation.directed:
      directed_expr = '>'
   else:
      directed_expr = ''
   q.write('MERGE (from)-[r{labels}]-{directed}(to)'.format(labels=':' + ':'.join(relation.labels) if len(relation.labels)>0 else '',directed=directed_expr))
   first = True
   for key in relation.properties.keys():
      if first:
         q.write('\n ON CREATE\n SET ')
         first = False
      else:
         q.write(',\n     ')
      value = relation.properties.get(key)
      if type(value)==str:
         value = cypher_literal(value)
      q.write('r.`{name}` = {value}'.format(name=key,value=value))
   return q.getvalue()

def cypher_for_node(node,merge=True):

   q = StringIO()
   if merge:
      q.write('MERGE (n{labels}'.format(labels=':'+':'.join(node.labels) if len(node.labels)>0 else ''))
      if len(node.keys)>0:
         q.write(' {')
         for index,id_property in enumerate(node.keys):
            value = node.properties.get(id_property)
            if value is None:
               raise ValueError('Node {id} is missing id property {id_property}'.format(id=id,id_property=id_property))
            if type(value)==str:
               value = cypher_literal(value)
            if index>0:
               q.write(', ')
            q.write('{id_property}: {value}'.format(id_property=id_property,value=value))
         q.write('}')
      q.write(')')
   else:
      q.write('CREATE (n:{labels})'.format(labels=':'+':'.join(node.labels) if len(node.labels)>0 else ''))

   first = True
   for property in node.properties.keys():
      if merge and property in node.keys:
         continue
      value = node.properties[property]
      if type(value)==dict:
         property, value = _get_property(value)
      # TODO: quote property name
      if first:
         if merge:
            q.write('\n ON CREATE\n')
         q.write(' SET ')
         first = False
      else:
         q.write(',\n     ')
      q.write('n.`{property}` = '.format(property=property))
      if type(value)==str:
         q.write(cypher_literal(value))
      else:
         q.write(str(value))
   return q.getvalue()

def cypher_for_item(item,merge=True):
   if type(item)==NodeItem:
      return cypher_for_node(item,merge=merge)
   elif type(item)==EdgeRelationItem:
      return cypher_for_edge_relation(item,merge=merge)

def graph_to_cypher(stream, merge=True):
   if isinstance(item, Generator) or isinstance(item, Iterator):
      for item in stream:
         yield cypher_for_item(item,merge=merge)
   else:
      yield cypher_for_item(item,merge=merge)

def _read_property_defs(fieldnames):
   property_defs = {}
   for property in fieldnames:
      if property[0]=='~':
         continue
      name, *typeinfo = property.split(':')
      type_name = typeinfo[0] if len(typeinfo)>0 else 'String'
      if type_name=='Int':
         type_func = int
      elif type_name=='Float':
         type_func = float
      else:
         type_func = str
      property_defs[property] = (name,type_func)
   return property_defs

def read_csv(source, location=None, schema=None, kind=None):
   reader = csv.DictReader(source,delimiter=',',quotechar='"')
   is_node = kind=='node'
   keys = set(['id'])
   property_defs = None
   for row in reader:
      if kind is None:
         if '~from' in row:
            is_node = False
         else:
            is_node = True
      if property_defs is None:
         property_defs = _read_property_defs(reader.fieldnames)
      if is_node:
         labels = set([row['~label']])
         properties = { 'id' : row['~id']}
         for property in property_defs:
            property_def = property_defs[property]
            properties[property_def[0]] = property_def[1](row[property])
         yield NodeItem(labels,keys,properties)
      else:
         properties = { 'id' : row['~id']}
         labels = set([row['~label']])
         for property in property_defs:
            property_def = property_defs[property]
            properties[property_def[0]] = property_def[1](row[property])
         yield EdgeRelationItem(labels,set(),{'id': row['~from']},set(),{'id': row['~to']},True,properties)


def read_graph(source, location=None,schema=None,format='yaml',kind=None):

   if format == 'csv':
      for item in read_csv(source, location=location, schema=schema,kind=kind):
         yield item
      return
   elif format != 'yaml':
      raise ValueError('Unrecognized format {}'.format(format))
   location = None
   if type(source)==tuple:
      location = source[1]
      source = source[0]

   if type(source)!=dict:
      source = yaml.load(source,Loader=yaml.Loader)

   if schema is None:
      schema_source = source.get('~schema')
      if schema_source is not None:
         parser = SchemaParser()
         if type(schema_source)==str:
            schema = parser.parse(schema_source)
         elif type(schema_source)==dict:
            fileref = schema_source.get('source')
            if fileref is not None:
               if location is not None:
                  dir = os.path.dirname(os.path.abspath(location))
                  fileref = os.path.join(dir,fileref)
               with open(fileref,'r') as input:
                  schema = parser.parse(input)
      if schema is not None:
         yield schema

   graph_edges = []
   for id in source.keys():
      if id == '~edges':
         graph_edges.append(source[id])
         continue
      if id[0] == '~':
         continue

      node = source[id]

      edges = node.get('~edges')
      if edges is not None:
         graph_edges.append((id,edges))

      labels = _label_list(node)

      keys = _get_id_properties(schema,labels)

      properties = {}

      for property in _node_properties(node):
         value = node[property]
         if type(value)==dict:
            property, value = _get_property(value)
         properties[property] = value

      if keys is None or len(keys)==0:
         keys = properties.keys()

      yield NodeItem(labels,keys,properties)

   for edges_spec in graph_edges:
      if type(edges_spec)==tuple:
         # node specific edges
         from_id = edges_spec[0]
         for edge in edges_spec[1]:
            to_id = edge.get('~to')
            directed = edge.get('~directed',True)
            labels = _label_list(edge)
            yield _create_edge(source, schema, from_id, to_id, directed, labels, edge)
      elif type(edges_spec)==dict:
         for edge in edges_spec.values():
            to_id = edge.get('~to')
            from_id = edge.get('~from')
            directed = edge.get('~directed',True)
            labels = _label_list(edge)
            yield _create_edge(source, schema, from_id, to_id, directed, labels, edge)
      else:
         for edge in edges_spec:
            to_id = edge.get('~to')
            from_id = edge.get('~from')
            directed = edge.get('~directed',True)
            labels = _label_list(edge)
            yield _create_edge(source, schema, from_id, to_id, directed, labels, edge)

if __name__ == '__main__':
   import sys
   for file in sys.argv[1:]:
      with open(file,'r') as input:
         first = True
         for query in graph_to_cypher(read_graph(input)):
            if not first:
               print('---')
            print(query)
            first = False
