import yaml

import pytest

from propgraph import read_graph, NodeItem, EdgeRelationItem, Schema, NodeDefinition

GRAPH_A = """
A:
 ~label: Component
 id: 'A'
 name: 'Component A'
 use: 12
 ~edges:
 - ~to: B
   ~label: imports
 - ~to: C
   ~label: imports
B:
 ~label: Component
 id: 'B'
 name: 'Component B'
 use: 6
C:
 ~label: Component
 id: 'C'
 name: 'Component C'
 use: 7
~edges:
  e1:
    ~from: C
    ~to: B
    ~label: imports
"""

GRAPH_A_STREAM_NO_INFER = [
   NodeItem(labels={'Component'},keys={'use','id','name'},properties={'id':'A','name':'Component A','use':12}),
   NodeItem(labels={'Component'},keys={'use','id','name'},properties={'id':'B','name':'Component B','use':6}),
   NodeItem(labels={'Component'},keys={'use','id','name'},properties={'id':'C','name':'Component C','use':7}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'A', 'use': 12, 'name': 'Component A'}, to_labels={'Component'}, to_node={'id': 'B', 'use': 6, 'name': 'Component B'}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'A', 'use': 12, 'name': 'Component A'}, to_labels={'Component'}, to_node={'id': 'C', 'use': 7, 'name': 'Component C'}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'C', 'use': 7, 'name': 'Component C'}, to_labels={'Component'}, to_node={'id': 'B', 'use': 6, 'name': 'Component B'}, directed=True, properties={})
]

GRAPH_A_STREAM_INFER = [
   NodeItem(labels={'Component'},keys={'@id'},properties={'id':'A','name':'Component A','use':12}),
   NodeItem(labels={'Component'},keys={'@id'},properties={'id':'B','name':'Component B','use':6}),
   NodeItem(labels={'Component'},keys={'@id'},properties={'id':'C','name':'Component C','use':7}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'@id': None}, to_labels={'Component'}, to_node={'@id': None}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'@id': None}, to_labels={'Component'}, to_node={'@id': None}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'@id': None}, to_labels={'Component'}, to_node={'@id': None}, directed=True, properties={})
]

GRAPH_A_STREAM_SCHEMA = [
   NodeItem(labels={'Component'},keys={'id'},properties={'id':'A','name':'Component A','use':12}),
   NodeItem(labels={'Component'},keys={'id'},properties={'id':'B','name':'Component B','use':6}),
   NodeItem(labels={'Component'},keys={'id'},properties={'id':'C','name':'Component C','use':7}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'A'}, to_labels={'Component'}, to_node={'id': 'B'}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'A'}, to_labels={'Component'}, to_node={'id': 'C'}, directed=True, properties={}),
   EdgeRelationItem(labels={'imports'}, from_labels={'Component'}, from_node={'id': 'C'}, to_labels={'Component'}, to_node={'id': 'B'}, directed=True, properties={})
]

def generate_schema(labels : set[str],keys : dict[str,str]):
   schema = Schema()
   default_key = keys.get('',{'@id'})
   for label in labels:
      keys = keys.get(label,default_key)
      node_def = NodeDefinition(labels={label},keys=keys)
      schema.add_node(node_def)
   return schema

@pytest.fixture
def graph_a() -> dict:
   return yaml.load(GRAPH_A,Loader=yaml.Loader)

def test_read_graph_sources(graph_a : dict) -> None:
   for item_a, item_b in zip(read_graph(GRAPH_A),read_graph(graph_a)):
      assert item_a==item_b, f'Item not equal: {item_a}!={item_b}'

def test_read_graph_modes(graph_a) -> None:
   for item_a, item_b in zip(read_graph(graph_a),GRAPH_A_STREAM_NO_INFER):
      assert item_a==item_b, f'No infer - item not equal: {item_a}!={item_b}'

   for item_a, item_b in zip(read_graph(graph_a,infer=True),GRAPH_A_STREAM_INFER):
      assert item_a==item_b, f'Infer - item not equal: {item_a}!={item_b}'

def test_read_graph_with_schema(graph_a) -> None:
   schema = generate_schema({'Component'},{'':'id'})
   for item_a, item_b in zip(read_graph(graph_a,schema=schema),GRAPH_A_STREAM_SCHEMA):
      assert item_a==item_b, f'With schema - item not equal: {item_a}!={item_b}'

def test_read_graph_with_default_key(graph_a) -> None:
   for item_a, item_b in zip(read_graph(graph_a,infer=True,default_key='id'),GRAPH_A_STREAM_SCHEMA):
      assert item_a==item_b, f'With default_key - item not equal: {item_a}!={item_b}'
