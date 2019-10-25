import requests
import gzip
import os


def postVespa(line,docid):
  line = line.strip()
  response = requests.post('http://localhost:8080/document/v1/test/doc/docid/%i' % docid, data=line, headers={"Content-Type":"application/json"})

feed_files = [f for f in os.listdir(".") if f.endswith("json.gz")]
feed_files.sort()
docid=0
for file in feed_files:
  with gzip.open(file, 'rb') as f:
    for line in f:
      postVespa(line,docid)
      docid +=1

