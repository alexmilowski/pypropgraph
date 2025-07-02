import argparse
import sys
import yaml

from propgraph import read_graph, graph_to_cypher, cypher_for_item, SchemaParser, NodeItem, EdgeRelationItem

if __name__ == '__main__':

   argparser = argparse.ArgumentParser(description='propgraph')
   argparser.add_argument('--host',help='Redis host',default='0.0.0.0')
   argparser.add_argument('--port',help='Redis port',type=int,default=6379)
   argparser.add_argument('--password',help='Redis password')
   argparser.add_argument('--show-query',help='Show the cypher queries before they are run.',action='store_true',default=False)
   argparser.add_argument('--show-property',help='A property to display as a progress indicator')
   argparser.add_argument('--infer',help='Infer labels and keys from @type and @id',action='store_true',default=False)
   argparser.add_argument('--single-line',help='Show progress indicator as single line',action='store_true',default=False)
   argparser.add_argument('--graph',help='The graph name',default='test')
   argparser.add_argument('--format',help='The input format',default='yaml',choices=['yaml','csv'])
   argparser.add_argument('operation',help='The operation to perform',choices=['validate','cypher','load', 'schema.check', 'schema.doc'])
   argparser.add_argument('files',nargs='*',help='The files to process.')

   args = argparser.parse_args()

   if len(args.files)==0:
      sources = [sys.stdin]
   else:
      sources = args.files
   for source in sources:
      with open(source,'r') if type(source)==str else source as input:

         # if not args.operation.startswith('schema'):
         #    if args
         #    graph_data = yaml.load(input,Loader=yaml.Loader), source if type(source)==str else None
         # else:
         #    graph_data = None

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
            import redis
            r = redis.Redis(host=args.host,port=args.port,password=args.password)
            def run_query(q):
               return r.execute_command('GRAPH.QUERY',args.graph,q)

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
               except redis.exceptions.ResponseError as err:
                  print('Failed query:')
                  print(query)
                  raise err
         elif args.operation=='schema.check' or args.operation=='schema.doc':
            parser = SchemaParser()
            schema = parser.parse(input)

            if args.operation=='schema.doc':
               schema.documentation(sys.stdout)
