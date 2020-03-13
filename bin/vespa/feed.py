import requests
import gzip
import os
import concurrent.futures 

def postVespa(data):
  docid,line = data 
  line = line.strip()
  response = requests.post('http://localhost:8080/document/v1/test/doc/docid/%i' % docid, data=line, headers={"Content-Type":"application/json"})
  return response.status_code

feed_files = [f for f in os.listdir(".") if f.endswith("json.gz")]
feed_files.sort()
docid=0
nthreads=8

ok=0
notok=0
with concurrent.futures.ThreadPoolExecutor(max_workers=nthreads) as executor:
  for file in feed_files:
    with gzip.open(file, 'rb') as f:
      futures = [executor.submit(postVespa,data) for data in enumerate(f)]
      for result in concurrent.futures.as_completed(futures):
        if result.result() == 200:
          ok+=1
        else:
          notok+=1

print("Feed documents %i - ok %i - not ok %i" %(ok+notok,ok,notok))

