import argparse
import os
import sys
from typing import Any
import yaml

from propgraph import read_graph, graph_to_cypher, cypher_for_item, SchemaParser, NodeItem, EdgeRelationItem
from .util import stringify_param_value

def main():
   argparser = argparse.ArgumentParser(description='propgraph')
   argparser.add_argument('--host',help='The database host (defaults to 0.0.0.0)',default='0.0.0.0')
   argparser.add_argument('--port',help='The database port (defaults to 6379)',type=int,default=6379)
   argparser.add_argument('--password',help='The database password (or DBPASSWORD environment variable)')
   argparser.add_argument('--username',help='The database username (or DBUSER environment variable)')
   argparser.add_argument('--show-query',help='Show the cypher queries before they are run.',action='store_true',default=False)
   argparser.add_argument('--show-property',help='A property to display as a progress indicator')
   argparser.add_argument('--infer',help='Infer labels and keys from @type and @id',action='store_true',default=False)
   argparser.add_argument('--single-line',help='Show progress indicator as single line',action='store_true',default=False)
   argparser.add_argument('--graph',help='The graph name',default='test')
   argparser.add_argument('--database',help='The database type (defaults to falkor)',default='falkordb',choices=['redis','falkordb'])
   argparser.add_argument('--format',help='The input format (defaults to yaml)',default='yaml',choices=['yaml','csv'])
   argparser.add_argument('operation',help='The operation to perform',choices=['validate','cypher','load', 'schema.check', 'schema.doc'])
   argparser.add_argument('files',nargs='*',help='The files to process.')

   args = argparser.parse_args()

   if len(args.files)==0:
      sources = [sys.stdin]
   else:
      sources = args.files
   for source in sources:
      with open(source,'r') if type(source)==str else source as input:

         if args.operation=='validate':
            # TODO: support multi-key nodes
            by_key = dict()
            by_label = set()
            for item in read_graph(input,format=args.format,infer=args.infer):
               if type(item)==NodeItem:
                  multi_key = ','.join([str(item.properties[key]) for key in sorted(item.keys)])
                  by_key[multi_key] = item.labels
                  for label in item.labels:
                     by_label.add(label)
                  by_label.add(':'.join(item.labels))
               elif type(item)==EdgeRelationItem:
                  for ids, labels in [(item.from_node,item.from_labels),(item.to_node,item.to_labels)]:
                     if len(ids)>0:
                        multi_key = ','.join([str(ids[key]) for key in sorted(ids.keys())])
                        node = by_key.get(multi_key)
                        if node is None:
                           print('Undefined node with properties {}.'.format(str(ids)),file=sys.stderr)
                     else:
                        label_key = ':'.join(labels)
                        if label_key not in by_label:
                           print('Undefined node with labels {}.'.format(':'.join(labels)),file=sys.stderr)

         elif args.operation=='cypher':

            for query in graph_to_cypher(read_graph(input,format=args.format,infer=args.infer)):
               print(query,end=';\n')

         elif args.operation=='load':
            password = args.password if args.password else os.environ.get('DBPASSWORD')
            username = args.username if args.username else os.environ.get('DBUSER')
            match args.database:
               case 'falkordb':
                  try:
                     import falkordb
                  except ModuleNotFoundError:
                     print('redis module was not installed. Install with: pip install pypropgraph[falkordb]',file=sys.stderr)
                     sys.exit(1)
                  db = falkordb.FalkorDB(host=args.host,port=args.port,username=username,password=password)
                  graph = db.select_graph(args.graph)
                  def run_query(q: str, params: dict[str,Any] | None = None):
                     return graph.query(q,params)
               case 'redis':
                  try:
                     import redis
                  except ModuleNotFoundError:
                     print('redis module was not installed. Install with: pip install pypropgraph[redis]',file=sys.stderr)
                     sys.exit(1)
                  db = redis.Redis(host=args.host,port=args.port,username=username,password=password)
                  # Note: a hack for backwards compatibility since RedisGraph is no longer a product
                  def run_query(q: str, params: dict[str,Any] | None = None):
                     if params:
                        params_header = "CYPHER "
                        for key, value in params.items():
                              params_header += str(key) + "=" + stringify_param_value(value) + " "
                        q = params_header + q
                     return db.execute_command('GRAPH.QUERY',args.graph,q)

            item_count = 0

            for item in read_graph(input,format=args.format,infer=args.infer):
               item_count += 1
               query = cypher_for_item(item)
               if query is None:
                  continue
               if args.show_query:
                  print(query)
                  print(';')
               if args.show_property is not None:
                  value = item.properties.get(args.show_property)
                  if value is not None:
                     print('({}) {}'.format(str(item_count),value),end='\r' if args.single_line else '\n')
               try:
                  run_query(query)
               except Exception as err:
                  print(f'Failed query:\n{query}',file=sys.stderr)
                  print(err,file=sys.stderr)
                  sys.exit(1)

         elif args.operation=='schema.check' or args.operation=='schema.doc':
            parser = SchemaParser()
            schema = parser.parse(input)

            if args.operation=='schema.doc':
               schema.documentation(sys.stdout)

if __name__ == '__main__':

   main()
