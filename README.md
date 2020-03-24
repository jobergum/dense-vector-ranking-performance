# Performance evaluation of nearest neighbor search using Vespa and Elasticsearch

In this repository we benchmark the performance of the dense vector type in Elastic and compare it with 
[Vespa.ai](https://vespa.ai/)'s [tensor field support and tensor operations](https://docs.vespa.ai/documentation/tensor-user-guide.html). 

Elastic recently released support for dense and sparse vectors of up to 1024 dimensions ,see  
[Elastic Blog:Text similarity search with vector fields](https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch). The 
sparse tensor type has later been deprecated. We evaluate the performance of performing nearest neighbor search using [euclidean distance](https://en.wikipedia.org/wiki/Euclidean_distance) with both Vespa and Elasticsearch.

## License
This work is published under APACHE 2.0  https://www.apache.org/licenses/LICENSE-2.0 

# Introduction 

Fast searching for the nearest neighbors of a data point in high dimensional vector space is an important problem for many real time applications. 
For example, in Computer Vision, searching for close data points in high dimensional vector space enables finding the most similar cats or faces in large image datasets. 
In Information Retrieval, large pre-trained multilingual natural language understanding models like BERT, allows representing text sentences in 
[dense embedding space](https://github.com/UKPLab/sentence-transformers), where nearest neighbor search could serve as an effective multilingual semantic retrieval function.

In many of these real word applications of (approximate) nearest neighbor search, the search is constrained by real time query filters applied over the data point’s metadata. 
For example, in E-Commerce search applications with constantly evolving metadata, a search for nearest products for a query in vector space would typically be constrained by 
product metadata like inventory status and price. 
There are many open source libraries and algorithms which provide fast approximate (A)NNS, [FAISS](https://github.com/facebookresearch/faiss) and [Annoy](https://github.com/spotify/annoy)
are examples of popular (A)NNS implementations. However these libraries, lacks support for efficient [metadata filtering](https://github.com/facebookresearch/faiss/wiki/FAQ#is-it-possible-to-dynamically-exclude-vectors-based-on-some-criterion) 
during the search in vector space. Search engines on the other hand, are designed for efficient evaluation of boolean query constraints over indices at scale,
but have historically had limited support for storing and indexing vectors or generally, tensor fields. 

## Datasets

Two datasets are evaluated, datasets which are commonly used when evaluating performance and accuracy of ANN, these datasets are obtained from a great resource on ANN benchmarks [https://github.com/erikbern/ann-benchmarks](https://github.com/erikbern/ann-benchmarks).

| Dataset                                                           | Dimensions | Train size | Test size | Neighbors | Distance  | Download                                                                   |
| ----------------------------------------------------------------- | ---------: | ---------: | --------: | --------: | --------- | -------------------------------------------------------------------------- |
| [GIST](http://corpus-texmex.irisa.fr/)                            |        960 |  1,000,000 |     1,000 |       100 | Euclidean | [HDF5](http://ann-benchmarks.com/gist-960-euclidean.hdf5) (3.6GB)          |
| [SIFT](https://corpus-texmex.irisa.fr/)                           |        128 |  1,000,000 |    10,000 |       100 | Euclidean | [HDF5](http://ann-benchmarks.com/sift-128-euclidean.hdf5) (501MB)          |

The datasets are split in a train and test, we index the train document corpus and evaluate the query performance using the vectors in the test set as queries. 
The task we want to accomplish with both engines is to compute the 10 nearest neighbors as measured by the euclidean distance between the document and query vector. Since both engines rank vectors/documents by decreasing relevance/score we use 1/(1+euclidean distance) as our scoring/ranking function. 

## Configuration and setup 
Building on the official docker images of Elasticsearch and Vespa.ai we build two custom docker images with the configuration. Using docker enables us to run the benchmark on the same hardware.

We use [vespa-fbench](https://docs.vespa.ai/documentation/performance/fbench.html) benchmarking client 
as it's already distributed with the Vespa docker image and is simple to use and supports HTTP POST. 
Both engines have similar HTTP based APIs for feed and search and we parse the hdf5 formatted datasets to Vespa and Elastic Json formats for both query and feed. The HDF5 data files published on [http://ann-benchmarks.com](http://ann-benchmarks.com)
are divided into a train set and a test set, we use index the vectors in the train set and use the test set vectors for benchmarking performance and accuracy metrics. 

### Feed API 
Both Vespa and Elastic have similar HTTP JSON apis for feeding documents. Below snippet is from [make-feed.py](bin/make-feed.py):
```python 
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

```

### Search API
Both Vespa and Elastic have similar HTTP JSON query apis for searching. Below snippet is from [make-queries.py](bin/make-queries.py) which generates the query input to the vespa-fbench HTTP benchmarking client.
```python
#Iterate over test vectors and generate json formatted POST query for ES and Vespa 
for v in test:
  query_vector = v.tolist() 
  vespa_body_ann = {
    'yql': 'select * from sources * where [{"targetNumHits":%i}]nearestNeighbor(vector,vector);' % 10,
    'hits': 10,
    'ranking.features.query(vector)': query_vector, 
    'ranking.profile': 'euclidean-rank',
    'summary': 'id',
    'timeout': '5s' 
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
    'timeout': '5s',
    'query': es_script_query
  }
  es_queries.write('/doc/_search\n')
  es_queries.write(json.dumps(es_body) + '\n')
  vespa_queries_ann.write('/search/\n')
  vespa_queries_ann.write(json.dumps(vespa_body_ann) + '\n')
```

### Elastic schema and configuration 
[index.json](config/elastic/index.json):
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "dynamic": "false",
    "_source": {
      "enabled": "false"
    },
    "properties": {
      "id": {
        "type": "integer"
      },
      "vector": {
        "type": "dense_vector",
        "dims":960 
      }
    }
  }
}
```
The Elastic service is started using 8GB of heap:
```
ES_JAVA_OPTS="-Xms8g -Xmx8g"
```

### Vespa schema and configuration 
#### Document definition
[doc.sd](config/vespa/searchdefinitions/doc.sd):
```
search doc {
  document doc {
    field id type int {
      indexing: summary |attribute
    }

    field vector type tensor<float>(x[960]) {
      indexing: attribute
    }
  }
  document-summary id {
    summary id type int { source: id}
  }
  rank-profile euclidean-rank inherits default {
    first-phase {
      expression: 1/(1 + sqrt(sum(join(query(vector), attribute(vector), f(x,y)((x-y)*(x-y))))))
    }
  }
}
```
#### Vespa application package 
* [services.xml](config/vespa/services.xml)
* [query profile](config/vespa/search/query-profiles/default.xml)
* [tensor query definition](config/vespa/search/query-profiles/types/root.xml)
* [doc.sd](config/vespa/searchdefinitions/doc.sd)

## Benchmark Results

## gist-960-euclidean Results

The following results were obtained on an instance with 1 x Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.30GHz (Ivy Bridge) 

### single shard with Elastic and threads-per-search equal to one with Vespa

| Engine                                                            | QPS        | Average Latency (ms) | 95P Latency (ms) | Recall@10 | 
| ----------------------------------------------------------------- | ---------: | -------------------: | ---------------: | --------: |  
| Elastic 7.6                                                       | 0.39       |  2547.42             |   2664.05        | 1.0000    |
| Vespa   7.190.14                                                  | 0.63       |  1572.29             |   1737.99        | 1.0000    |

The following results were obtained on an instance with 1 x Intel(R) Xeon E5-2680 v3 2.50GHz (Haswell)

### single shard with Elastic and threads-per-search equal to one with Vespa

| Engine                                                            | QPS        | Average Latency (ms) | 95P Latency (ms) | Recall@10 | 
| ----------------------------------------------------------------- | ---------: | -------------------: | ---------------: | --------: |  
| Elastic 7.6                                                       | 0.57       |  1752.74             |   1850.74        | 1.0000    |
| Vespa   7.190.14                                                  | 1.32       |   756.61             |    955.63        | 1.0000    |


## sift-128-euclidean Result
The following results were obtained on an instance with 1 x Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.30GHz (Ivy Bridge) 

### single shard with Elastic and threads-per-search equal to one with Vespa

| Engine                                                            | QPS        | Average Latency (ms) | 95P Latency (ms) | Recall@10 | 
| ----------------------------------------------------------------- | ---------: | -------------------: | ---------------: | --------: |  
| Elastic 7.6                                                       | 2.01       |   496.42             |    555.34        | 1.0000    |
| Vespa   7.190.14                                                  | 4.03       |   248.29             |    316.40        | 1.0000    |


The following results were obtained on an instance with 1 x Intel(R) Xeon E5-2680 v3 2.50GHz (Haswell)

### single shard with Elastic and threads-per-search equal to one with Vespa

| Engine                                                            | QPS        | Average Latency (ms) | 95P Latency (ms) | Recall@10 | 
| ----------------------------------------------------------------- | ---------: | -------------------: | ---------------: | --------: |  
| Elastic 7.6                                                       | 3.29       |   303.96             |    337.89        | 1.0000    |
| Vespa   7.190.14                                                  | 9.14       |   109.33             |    148.90        | 1.0000    |


### Benchmark parameters
<pre>
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa \
  -P -H "Content-Type:application/json" -q /tmp/queries/elastic/queries.txt -s 180 -n 1 -c 0 -i 20 -o /tmp/queries/result.es.txt localhost 9200 
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa \
  -P -H "Content-Type:application/json" -q /tmp/queries/vespa/queries.txt -s 180 -n 1 -c 0 -i 20 -o /tmp/queries/result.vespa.txt localhost 8080 
</pre>

Parameter explanation :
* -s 180 run for 180 seconds
* -n 1 one client (No concurrency, sequential execution)
* -c 0 No client wait, fire a new query when the previous has completed
* -i 20 Ignore the latency of the first 20 queries to allow warmup 
* -q input query file as generated by the make-queries.py 
* -P use HTTP POST 
* -H Header for JSON formatted POST body 


## Reproducing the benchmarks  
The benchmark can be reproduced using [Dockerfile.vespa](Dockerfile.vespa) and [Dockerfile.elastic](Dockerfile.elastic).
Both images are built on the official [elasticsearch](https://hub.docker.com/_/elasticsearch) and [vespa](https://hub.docker.com/r/vespaengine/vespa/) docker images. The following reproduces
the benchmark using the gist-960-euclidean dataset with 960 dimensions.

**Requirements:**

* [Docker](https://www.docker.com/) installed and running. Script usage assumes Linux/Mac OS X host system. 
* git client to checkout this repository and wget installed to download the dataset(s)
* python3 to convert the data into Vespa and Elastic feed and query json format (Also h5py and requests library, obtain with pip3 install h5py requests)
* Ensure you have enough memory available. The Vespa container needs about 5GB and the Elastic container is configured with 8GB heap so 10GB should be about sufficient. 

## Instructions to reproduce benchmark on sift 1M vector data set
Clone, build containers and run.  
<pre>
$ git clone https://github.com/jobergum/dense-vector-ranking-performance.git; cd dense-vector-ranking-performance
$ ./bin/build.sh 
$ ./bin/run.sh
$ wget http://ann-benchmarks.com/gist-960-euclidean.hdf5
</pre>

Verify that the two docker containers are running:
<pre>
$ docker ps |egrep "vespa|es"
</pre>

### Deploy configuration and document schema 
#### Vespa
Verify that configuration service is running and returns 200 OK:
<pre>
$ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
</pre>
Upload the Vespa application package with document schema: 
<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare config && \
    /opt/vespa/bin/vespa-deploy activate'
</pre>

#### Elastic
Verify that Elastic service is running and returns 200 OK:
<pre>
$ docker exec es bash -c 'curl -s --head http://localhost:9200/'
</pre>
Deploy Elastic index schema 
<pre>
$ docker exec es bash -c '/usr/share/elasticsearch/create-index.sh'
</pre>

### Feed data
Both Vespa and Elastic has batch oriented feed api's with higher throughput performance but
to keep the dependency list short we opt to use the simplistic HTTP based apis. Feeding 
<pre>
$ python3 ./bin/make-feed.py gist-960-euclidean.hdf5 
</pre>
Make both engines, merge the segments within the shard for Elastic and flush and merge the memory index for Vespa.
<pre>
$ curl -s -X POST "http://localhost:9200/doc/_forcemerge?max_num_segments=1"
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-proton-cmd --local triggerFlush'
</pre>


### Run benchmark 
<pre>
$ python3 ./bin/make-queries.py gist-960-euclidean.hdf5 
$ ./bin/do-benchmark.sh 
</pre>

### Check recall 
<pre>
$ python3 ./bin/check-recall.py gist-960-euclidean.hdf5 
</pre> 

