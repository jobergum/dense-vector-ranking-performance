import numpy as np
import json
import gzip as gz

chunks = 3
docid=0
for chunk_id in range(0,chunks):
  es_feed = gz.open("elastic/feed-%i.json.gz" % chunk_id, "wb")
  vespa_feed = gz.open("vespa/feed-%i.json.gz" % chunk_id, "wb")
  for i in range(0, 20000):
    doc_vector = np.random.rand(1,512)[0]
    norm = np.linalg.norm(doc_vector)
    doc_vector = doc_vector/norm
    doc_vector = doc_vector.tolist()
    vespa_body = {
      "fields": {
        "text_embedding": {
          "values":  doc_vector
        },
        "id": docid 
      }
    }

    es_body={
      "id": docid,
        "text_embedding": doc_vector
    }
    es_feed.write((json.dumps(es_body) + "\n").encode("utf-8"))
    vespa_feed.write((json.dumps(vespa_body) + "\n").encode("utf-8"))
    docid+=1
  es_feed.close()
  vespa_feed.close()

