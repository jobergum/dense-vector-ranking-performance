import h5py
import sys
import concurrent.futures 
import requests

file= sys.argv[1]
train = h5py.File(file, 'r')['train']

def feed_to_es_and_vespa(data):
  docid,vector = data
  vector = vector.tolist()
  vespa_body = {
    "fields": {
      'vector': {
        'values': vector 
      },
      'id': docid
    }
  }
  es_body={
    'id': docid,
    'vector': vector 
  }
  response = requests.post('http://localhost:8080/document/v1/test/doc/docid/%i' % docid, json=vespa_body)
  response.raise_for_status()
  response = requests.post('http://localhost:9200/doc/_doc/%i' %docid, json=es_body)
  response.raise_for_status()

nthreads=18
with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
  futures = [executor.submit(feed_to_es_and_vespa,data) for data in enumerate(train)]
  for result in concurrent.futures.as_completed(futures):
    pass
