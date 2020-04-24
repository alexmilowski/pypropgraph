import yaml
from io import StringIO

def cypher_literal(value):
   return "'" + value.replace("'",r"\'") + "'"

def _label_list(spec):
   labels = spec.get('~label')
   if labels is None:
      labels = []
   if type(labels)!=list:
      labels = [labels]
   return labels

def _get_id_property(schema,labels):
   if schema is not None:
      for label in labels:
         node_spec = schema.get(label)
         if node_spec is not None:
            break

   return node_spec.get('~id') if node_spec is not None else None

def _create_edge(source, schema, from_id, to_id, directed, labels, edge):
   from_node = source.get(from_id)
   if from_node is None:
      raise ValueError('Cannot find node with id '+from_id)
   to_node = source.get(to_id)
   if to_node is None:
      raise ValueError('Cannot find node with id '+to_id)
   q = StringIO()
   for label, id, node in [('from',from_id,from_node),('to',to_id,to_node)]:
      labels = _label_list(node)
      id_property = _get_id_property(schema,labels)
      if id_property is not None:
         value = node.get(id_property)
         if value is None:
            raise ValueError('Node {id} has not id property {property}'.format(id=id,property=id_property))
         if type(value)==str:
            value = cypher_literal(value)
         q.write('MERGE ({label}:{labels} {{ {property}: {value} }})\n'.format(label=label,labels=':'.join(labels),property=id_property,value=value))
      else:
         q.write('MERGE ({label}:{labels})\n'.format(label=label,labels=':'.join(labels)))
   if directed:
      directed_expr = '>'
   else:
      directed_expr = ''
   q.write('MERGE (from)-[r:{labels}]-{directed}(to)'.format(labels=':'.join(_label_list(edge)),directed=directed_expr))
   first = True
   for key in edge.keys():
      if key[0]=='~':
         continue
      if first:
         q.write(' ON CREATE SET\n')
         first = False
      else:
         q.write(',\n')
      value = edge.get(key)
      if type(value)==str:
         value = cypher_literal(value)
      # TODO: escape property name
      q.write('r.{name} = {value}'.format(name=key,value=value))
   return q.getvalue()


def graph_to_cypher(source, merge=True):

   if type(source)!=dict:
      source = yaml.load(source,Loader=yaml.Loader)

   schema = source.get('~schema')

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

      id_property = _get_id_property(schema,labels)

      q = StringIO()
      if merge and id_property is not None:
         value = node.get(id_property)
         if value is None:
            raise ValueError('Node {id} is missing id property {id_property}'.format(id=id,id_property=id_property))
         if type(value)==str:
            value = cypher_literal(value)
         q.write('MERGE (n:{labels} {{ {id_property}: {value} }})\nON CREATE\n'.format(labels=':'.join(labels),id_property=id_property,value=value))
      else:
         q.write('CREATE (n:{labels})\n'.format(labels=':'.join(labels)))

      first = True
      for property in node.keys():
         if property[0]=='~':
            continue
         if merge and id_property==property:
            continue
         value = node[property]
         # TODO: quote property name
         if first:
            q.write('SET ')
            first = False
         else:
            q.write(',\n    ')
         q.write('n.{property} = '.format(property=property))
         if type(value)==str:
            q.write(cypher_literal(value))
         else:
            q.write(str(value))
      if first:
         q.write('\n')

      yield q.getvalue()

   for edges_spec in graph_edges:
      if type(edges_spec)==tuple:
         # node specific edges
         from_id = edges_spec[0]
         for edge in edges_spec[1]:
            to_id = edge.get('~to')
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
         for query in graph_to_cypher(input):
            if not first:
               print('---')
            print(query)
            first = False
