import numpy as np
import json

es_queries = open("es_queries.txt","w")
vespa_queries = open("vespa_queries.txt","w")

for i in range(0,1000):
  query_vector = np.random.rand(1,512)[0]
  norm = np.linalg.norm(query_vector)
  query_vector = query_vector/norm
  query_vector = query_vector.tolist()
  vespa_body = {
    "query": "sddocname:doc",
    "hits": 5,
    "ranking.features.query(tensor)": query_vector, 
    "ranking.profile": "dotProduct",
    "summary": "id" 
  }

  es_script_query = {
    "script_score": {
      "query": {"match_all": {}},
      "script": {
        "source": "dotProduct(params.query_vector, doc['text_embedding']) + 1.0",
        "params": {"query_vector": query_vector}
      }
    }
  }
  es_body={
    "size": 5,
    "query": es_script_query
  }
  es_queries.write("/doc/_search\n")
  es_queries.write(json.dumps(es_body) + "\n")

  vespa_queries.write("/search/\n")
  vespa_queries.write(json.dumps(vespa_body) + "\n")

