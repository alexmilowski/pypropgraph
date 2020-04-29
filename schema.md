# Describing Property Graphs with a Schema

## Scope of usage

The schema format described before has some basic goals:

 * a simple syntax for describe the nodes, edges, and properties
 * provide a way to annotate nodes, edges, and properties with documentation
 * describe identity properties on nodes for match/merge queries

While a schema can be used for validation purposes, the lack of node
labels, properties, or cardinality constraints limits the use in that context.

## An illustrative example

```
'''
# Ontology Graph

A property graph for ontologies based on OBO/OWL ontology structures.

'''

(:Ontology {id})
'''The root of the ontology'''
.id                = 'an identifier for the ontology in the graph'
.data-version      = 'a version string'
.date              = datetime 'the creation date of the ontology'
.default-namespace = 'the default namespace to use for the ontology'
.format-version    = 'the input format version'
.ontology          = 'the identifier for the ontology which may be the same as the id'
.remark            = 'a comment'
.saved-by          = 'an identification of the process that generated the format'
-[:subsetdef]->(:Subset) = '''
A subset of the ontology. Terms identify themselves as member of a subset.
'''
-[:term]->(:Term) = 'a term belonging to the ontology'
-[:typedef]->(:Typedef) = 'a type definition belonging to the ontology'

(:Term {id})
.id = 'an identifier for the term in the graph. This is often the same as `name`'
.name = 'the term identifier in the ontology'
.comment
.created_by
.creation_date
.def
.is_obsolete
-[:alias]->(:Term)
-[:def]->(:Resource)
-[:subset]->(:Subset)
-[:synonym]->(:XRef)
-[:xref]->(:XRef)
-[:is_a]->(:Term)
-[:disjoint_from]->(:Term)

(:Typedef {id})
.name
.def
-[:def]->(:Resource)

(:Resource {url})

(:Subset {id})
.description

(:XRef {id})
.relation
.related
```

## Syntax overview

### Literals

```
literal: string | long_string
```

Literals can be single line (`string`) with a single quote:

```
'a single line'
```

or multi-line (`long_string`) with triple single quotes:

```
'''
All the world ‘s a stage, and all the men and women merely
players. They have their exits and their entrances; And one
man in his time plays many parts
'''
```

### Names and identifiers

Labels follow the same constraints as [Open Cypher](https://www.opencypher.org) and can start with an identifier start character (e.g., [a-zA-Z_]) followed by other identifier characters.

Property names can either be similar simple identifiers or can be quoted with
the back-tick (\`) for values that have non-identifier characters.

```
label: NAME
type: NAME
property_name: NAME | BACKQUOTE_STRING
```

### Comments

A comment starts with a '#' character and extends to the end of the line.

### Documentation literals

All documentation literals are strings and can include [Commonmark Markdown](https://commonmark.org) markup.

## Schema structure

### Schema definition

A schema can start with an optional documentation string and is followed by a set of node definitions.

```
schema: prolog? node*
prolog: literal
```

### Node definition

A node is defined by a set of node labels, a list of identity properties, and is follows by a set of node properties and edge relations.

```
node: "(" node_labels ("{" keys? "}")? ")" description? properties? relations?
node_labels: label+
keys: property_name ("," property_name)*
description: string | long_string
```

### Property definitions

A property starts with a period (.) character and typically follows a node or is
within a relationship definition.

The type specified is a simple identifier and contextual to the using system.

```
properties: property+
property: "." property_name ("=" type? description?)?
```

### Edge relation definitions

A edge relation is a pattern of the form `-[:label]->(:target_label)`. The properties for the relationship are defined within the square brackets.

```
relations: relation+
relation: "-" "[" relation_labels properties? "]" direction "(" target_nodes? ")" ("=" description?)?
relation_labels: label+
direction: "-" | "->"
```

For example:

```
(:Element {name})
'''
An element used in some document instances.
'''
.name = 'The element name'
-[ :child .use = int 'A count of usage' ]->(:Element,:Text) = 'A child element relation.'
```
