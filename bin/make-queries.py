import numpy as np
import json
import h5py
import sys

file= sys.argv[1]
test= h5py.File(file, 'r')['test']

es_queries = open('data/elastic/queries.txt', 'w')
vespa_queries_ann = open('data/vespa/queries_ann.txt', 'w')

for v in test:
  query_vector = v.tolist() 
  vespa_body_ann = {
    'yql': 'select * from sources * where [{"targetNumHits":%i}]nearestNeighbor(vector,vector);' % 10,
    'hits': 10,
    'ranking.features.query(vector)': query_vector, 
    'ranking.profile': 'euclidean-rank',
    'summary': 'id',
    'timeout': '15s',
    'ranking.softtimeout.enable': 'false' 
  }

  es_script_query = {
    'script_score': {
      'query': {'match_all': {}},
      'script': {
        'source': '1/(1 + l2norm(params.query_vector, doc[\'vector\']))',
        'params': {'query_vector': query_vector}
      }
    }
  }
  es_body={
    'size': 10,
    'timeout': '15s', 
    'query': es_script_query
  }
  es_queries.write('/doc/_search\n')
  es_queries.write(json.dumps(es_body) + '\n')

  vespa_queries_ann.write('/search/\n')
  vespa_queries_ann.write(json.dumps(vespa_body_ann) + '\n')
