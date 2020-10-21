# pypropgraph

A Property Graph library for python that supports reading and writing
property graphs in a textual format, reading an writing via Cypher, and
a simple schema language.

## Things you can do

 * generate documentation for your property graph structure
 * load, parse, and manipulate PG Schema documents
 * load saved graphs from a YAML format, schema embedded
 * generate cypher from saved graphs to load property graphs

## Install

You can install the package via:

```sh
pip install pypropgraph
```

## Using the command-line interface

The module can be invoked directly and provides a set of basic commands that
allow parsing, inspection, cypher statement generation, and loading ontologies.

The invocation is:

```sh
python -m propgraph {operation} {file ...}?
```

where `operation` is one of:

   * `validate` - parse and validate the graph
   * `cypher` - generate cypher create/merge statements
   * `load` - load the ontology into a property graph database
   * `schema.check` - check the syntax of a schema
   * `schema.doc` - generate Markdown documentation for the schema

If the file is omitted, the command will read from stdin. Otherwise, each
file specified will be read and operated on in the order they are specified.

## Loading property graphs

The module currently supports loading ontologies directly into [RedisGraph](https://github.com/RedisGraph/RedisGraph).

The following options can be specified for connecting to the database:

 * `--host {name}|{ip}` - the host of the database, defaults to 0.0.0.0
 * `--port {port}` - the port, defaults to 6379
 * `--password {password}` - the database password, default is no password
 * `--graph {key}` - the graph key, defaults to "test"
 * `--infer` - infer identity and labels from @id and @type, respectively

Adding the `--show-query` option will allow you to see the Cypher statements as
they are executed.

## Property graph YAML format

The YAML-based format is a simple dictionary of nodes and edges.

### Graphs

At the top-level, a **graph** is a dictionary whose keys define
the nodes, schema, and edges. The keys can either be:

 * `~schema` - the schema definition for the property graph
 * `~edges` - a set of fully qualified edges
 * {label} - a node label

```YAML
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
```


When a schema is specified via `~schema`, the properties that establish
the node's identity can be specified.

Alternatively, we can use inferencing and the edge label format:

```YAML
A:
 @type: Component
 @id: 'A'
 name: 'Component A'
 use: 12
 :imports:
 - ~to: B
 - ~to: C
B:
 @type: Component
 @id: 'B'
 name: 'Component B'
 use: 6
C:
 @type: Component
 @id: 'C'
 name: 'Component C'
 use: 7
:imports:
 - ~from: C
   ~to: B
```


### Nodes

A **node** is a simple dictionary whose key/value pairs define properties
all except for two special labels:

 * `~labels` - the set of Node labels
 * `~edges` - the edges connected to the node
 * {label} - a property

A **property** can either be a simple key/value pair where the key will be the
property name. It can also be defined with the `name:` and `value:` keys for
property name values that are harder to encode as a key:

```YAML
Funky:
  name: 'Town'
  p1:
     name: "Meaning of life"
     value: 42
```

Node can specify an edge via a label and enumerate the target nodes and edge
properties:


```YAML
A:
  id: 'A'
  :child:
    - ~to: B
      use: 1209
    - ~to: C
      use: 432
B:
  id: 'B'
  :child:
     e1:
        ~to: C
        use: 128
C:
  id: 'C'
```


Nodes can also specify a set of edges that originate at the node via the `~edges`
key. The edges are specified as a list or key labeled set:

```YAML
A:
  id: 'A'
  ~edges:
    - ~to: B
      ~label: child
      use: 1209
    - ~to: C
      ~label: child
      use: 432
B:
  id: 'B'
  ~edges:
     e1:
        ~to: C
        ~label: child
        use: 128
C:
  id: 'C'
```

### Edges

Edges can also be specified at the graph level instead of in the node. At the top-level, a single `~edges` key is allowed that can specify edges from and to nodes. The
`~from` key must also be specified:

```YAML
A:
  id: 'A'
B:
  id: 'B'
C:
  id: 'C'
~edges:
  - ~from: A
    ~to: B
    ~label: child
    use: 1209
  - ~from: A
    ~to: C
    ~label: child
    use: 432
  - ~from: B
    ~to: C
    ~label: child
    use: 128
```

Alternatively, you can specify a label for the edge and enumerate the edges associated with that label:

```YAML
A:
  id: 'A'
B:
  id: 'B'
C:
  id: 'C'
:child:
  - ~from: A
    ~to: B
    use: 1209
  - ~from: A
    ~to: C
    use: 432
  - ~from: B
    ~to: C
    use: 128
```

## Label and Identity Inference

Reusing the '@type' and '@id' properties from [JSON-LD](https://json-ld.org),
if these properties are specified on a node, then the following inferences
can be optionally applied:

 * The value of @type will turn into a node label
 * The value of @id will be used as the key for matching the node

 Otherwise, labels and identity must be accomplished via the schema.

### Schemas

A schema can be specified at the top-level via the `~schema` key. The schema itself is either embedded directly as text or has a single `source` key specifying the file location.

For example, in the imports graph example, the `id` property can be specified as
property that identifies the node. This can be helpful for generating merge or match queries.

The [schema format](schema.md) is described separately and allows you to define nodes, labels, properties, and their descriptions.

The schema can be embedded as text:

```YAML
~schema: |
  (:Component {id})
  .id = 'the component identifier'
  .name = 'the component descriptive name'
  .use = int 'a count of usage'
  -[:imports]->(:Component) = 'an imported component'
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
  - ~from: C
    ~to: B
    ~label: imports
```

or via reference:

```YAML
~schema:
  source: schema.pgs
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
  - ~from: C
    ~to: B
    ~label: imports
```

## API

### Loading Graphs

The graph source is just raw YAML and should be loaded directly using the `yaml` package:

```python
import yaml

with open('graph.yaml','r') as input:
   graph_data = yaml.load(input,Loader=yaml.Loader)
```

Once you have loaded the graph YAML, you can read the graph into a sequence
of item (NodeItem or EdgeRelationItem):

```python
import yaml
from propgraph import read_graph

with open('graph.yaml','r') as input:
   graph_data = yaml.load(input,Loader=yaml.Loader)
   for item in read_graph(graph_data):
      print(item)
```

These items can be turned into cypher merge or create statements:

```python
import yaml
from propgraph import read_graph, graph_to_cypher

with open('graph.yaml','r') as input:
   graph_data = yaml.load(input,Loader=yaml.Loader)
   for query in graph_to_cypher(read_graph(graph_data)):
      print(query,end=';\n')
```

Finally, the graph can easily be loaded into RedisGraph:

```python
import yaml
from propgraph import read_graph, graph_to_cypher

import redis
from redisgraph import Graph
r = redis.Redis(host='localhost',port=6379,password='...')
rg = Graph('test',r)

with open('graph.yaml','r') as input:
   graph_data = yaml.load(input,Loader=yaml.Loader)
   for query in graph_to_cypher(read_graph(graph_data)):
      rg.query(query)
```

### Loading Schemas

A schema can be loaded from a file:

```python
from propgraph import SchemaParser

parser = SchemaParser()
with open('schema.pgs','r') as input:
   schema = parser.parse(input)
```

or a string:

```python
from propgraph import SchemaParser

source = '''
(:Component {id})
.id = 'the component identifier'
.name = 'the component descriptive name'
.use = int 'a count of usage'
-[:imports]->(:Component) = 'an imported component'
'''

parser = SchemaParser()
schema = parser.parse(input)

```

### Generating schema documentation

Documentation in Markdown format can be generate from the schema object:

```python
import sys
from propgraph import SchemaParser

source = '''
(:Component {id})
.id = 'the component identifier'
.name = 'the component descriptive name'
.use = int 'a count of usage'
-[:imports]->(:Component) = 'an imported component'
'''

parser = SchemaParser()
schema = parser.parse(input)

schema.documentation(sys.stdout)

```

### API

Note: incomplete ...

`read_graph(source,location=None,schema=None)`

Reads a graph into a sequence of items

`graph_to_cypher(stream,merge=True)`

Transforms a sequence of items into a sequence of cypher statements

`cypher_for_node(item,merge=True)`

Returns a cypher statement to create a node from a node item.

`cypher_for_edge_relation(item,merge=True)`

Returns a cypher statement to create an edge from a edge relation item.

#### NodeItem

#### EdgeRelationItem

#### SchemaParser

#### Schema

#### NodeDefinition

#### EdgeDefinition
