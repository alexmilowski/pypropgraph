import argparse
import sys
import yaml

from propgraph import graph_to_cypher

if __name__ == '__main__':

   argparser = argparse.ArgumentParser(description='propgraph')
   argparser.add_argument('--host',help='Redis host',default='0.0.0.0')
   argparser.add_argument('--port',help='Redis port',type=int,default=6379)
   argparser.add_argument('--password',help='Redis password')
   argparser.add_argument('--show-query',help='Show the cypher queries before they are run.',action='store_true',default=False)
   argparser.add_argument('--graph',help='The graph name',default='test')
   argparser.add_argument('operation',help='The operation to perform',choices=['validate','cypher','load'])
   argparser.add_argument('files',nargs='*',help='The files to process.')

   args = argparser.parse_args()

   if len(args.files)==0:
      sources = [sys.stdin]
   else:
      sources = args.files
   for source in sources:
      with open(source,'r') if type(source)==str else source as input:
         graph_data = yaml.load(input,Loader=yaml.Loader)

         if args.operation=='validate':
            print('Not implemented',file=sys.stderr)

         elif args.operation=='cypher':

            for query in graph_to_cypher(graph_data):
               print(query)
               print(';')

         elif args.operation=='load':
            import redis
            from redisgraph import Graph
            r = redis.Redis(host=args.host,port=args.port,password=args.password)
            graph = Graph(args.graph,r)

            for query in graph_to_cypher(graph_data):
               if args.show_query:
                  print(query)
                  print(';')
               graph.query(query)
