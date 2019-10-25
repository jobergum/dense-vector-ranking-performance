# Vespa.ai and Elastic.co performance evaluation for dense vector dot product 

Elastic recently released support for dense and sparse vectors of up to 1024 dimensions [Elastic Blog:Text similarity search with vector fields](https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch).
In this repo we experiment and benchmark the performance of the dense vector representation in Elastic and compare it with [Vespa.ai](https://vespa.ai/)'s tensor field support and tensor operations.  We evaluate the performance of performing nearest neighbor ranking
over a set of 60K 512 dimensional vectors against a query set of 1K 512 dimensional query vectors using the dotProduct as the similarity function. Both the query and document vectors are normalized so the dot product score equals the cosine similarity 
which is typically used for nearest neighbor ranking. Both engines currently lack support for performing approximate nearest neighbor search (a-nn).  

## License
This work is published under APACHE 2.0  https://www.apache.org/licenses/LICENSE-2.0 

## Configuration and setup 
Using the published docker images for elasticsearch and vespa.ai we build two docker images building on the official images so that we can run the same benchmark setup with both engines using the same hardware. 
We randomly generate 60K 512-dimensional vectors using numpy which we index in both Elastic and Vespa using the respective HTTP based APIs. The task given is to compute the top-5 ranking documents using 
the dotProduct between the document and query vector as the ranking function. Vespa is configured to use 2 threads per search and Elastic configured with two shards. 

We use [vespa-fbench](https://docs.vespa.ai/documentation/performance/fbench.html) benchmarking client 
as it's already distributed with the vespa.ai image and is simple to use and supports HTTP POST with connection pooling. Both engines have similar HTTP based APIs (JSON feed formats and JSON response renders).

### Benchmark parameters

<pre>
echo "Elastic 7.4 Vector Similarity Search"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa -P -H "Content-Type:application/json" -q /tmp/queries/elastic/queries.txt -s 120 -n 1 -c 0 -i 20 -o /tmp/queries/result.es.txt localhost 9200 

echo "Vespa Vector Similarity Search"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa -P -H "Content-Type:application/json" -q /tmp/queries/vespa/queries.txt -s 120 -n 1 -c 0 -i 20 -o /tmp/queries/result.vespa.txt localhost 8080 
</pre>

Parameter explanation :
* -s 120 run for 120 seconds
* -n 1 one client (No concurrency, only measuring latency with no concurrency involved
* -c 0 No client wait, fire a new query when the previous has completed
* -i 20 Ignore the latency of the first 20 queries to allow JVM warmup (JiT)
* -q input query file 
* -P use HTTP POST 

## Benchmark Results

The following results were obtained on a instance with 1xIntel(R) Xeon(R) CPU E5-2630 0 @ 2.30GHz cpu and 24GB of memory.  

<pre>
Elastic 7.4 Vector Similarity Search

***************** Benchmark Summary *****************
clients:                       1
ran for:                     120 seconds
cycle time:                    0 ms
lower response limit:          0 bytes
skipped requests:              0
failed requests:               0
successful requests:         982
cycles not held:             982
minimum response time:    101.95 ms
maximum response time:    194.04 ms
average response time:    119.24 ms
25 percentile:            111.70 ms
50 percentile:            115.60 ms
75 percentile:            125.38 ms
90 percentile:            134.48 ms
95 percentile:            139.99 ms
99 percentile:            152.10 ms
actual query rate:          8.38 Q/s
utilization:               99.92 %
zero hit queries:              0
http request status breakdown:
       200 :     1002 

Vespa.ai Vector Similarity Search

***************** Benchmark Summary *****************
clients:                       1
ran for:                     120 seconds
cycle time:                    0 ms
lower response limit:          0 bytes
skipped requests:              0
failed requests:               0
successful requests:        5130
cycles not held:            5130
minimum response time:     19.82 ms
maximum response time:     44.79 ms
average response time:     23.12 ms
25 percentile:             21.50 ms
50 percentile:             22.40 ms
75 percentile:             23.50 ms
90 percentile:             25.70 ms
95 percentile:             29.90 ms
99 percentile:             33.60 ms
actual query rate:         43.08 Q/s
utilization:               99.61 %
zero hit queries:              0
http request status breakdown:
       200 :     5150 
</pre>

As seen from the above output from vespa-fbench the Vespa.ai engine is about 5 times faster than Elastic for this particular use case. Average latency is 119.24 ms for Elastic versus 23.12 ms for Vespa. 

Note that the obtained query rate is with 1 client and is simply a function of the average latency.
Also note that the average versus 95-99p latency does not differ significantly as each query recalls the same amount of documents (60K). Elastic seem to set a maximum of number of hits it collects and reports a hit count of 10K while Vespa calculates
the exact total count (60K). [Elastic doc tracking total hits](https://www.elastic.co/guide/en/elasticsearch/reference/7.0/search-request-track-total-hits.html )

Sample debug queries which demonstrates this:.

**Elastic**

<pre>
$ curl -X POST -s -H "Content-Type:application/json" -d @sample-queries/elastic.json http://localhost:9200/doc/_search |python -m json.tool
</pre>

**Vespa**
<pre>
$ curl -X POST -s -H "Content-Type:application/json" -d @sample-queries/vespa.json http://localhost:8080/search/ |python -m json.tool
</pre>


### Resource usage
We don't deep dive into the performance characteristics of the two engines but docker stats shows roughtly the same cpu usage for both during query bencmarking (Vespa with 2 threads per search using two cpu cores and one thread per shard for elastic) so
roughtly 200% usage for both. Elastic
was configured with a 8GB heap to make sure we did not run into any high GC pressure so the memory utilization can be ignored. Both engines could be configured to speed up the latency by increasing threads per search for Vespa and increasing number of shards
for elastic. 

<pre>
$ docker stats 
CONTAINER           CPU %               MEM USAGE / LIMIT       MEM %               NET I/O             BLOCK I/O           PIDS
es                  214.88%             8.578 GiB / 23.39 GiB   36.68%              6.87 MB / 431 kB    15.2 MB / 3.97 GB   88
vespa               203.26%             3.508 GiB / 23.39 GiB   15.00%              30.6 MB / 3.86 MB   131 MB / 847 MB     2093
</pre>

## How to reproduce the benchmark  
The benchmark comparision can be reproduced using the published Dockerfiles: [Dockerfile.vespa](Dockerfile.vespa) [Dockerfile.elastic](Dockerfile.elastic).

Both images are built on the official [elasticsearch](https://hub.docker.com/_/elasticsearch) and [vespa](https://hub.docker.com/r/vespaengine/vespa/) docker images.

**Requirements:**

* [Docker](https://www.docker.com/) installed and running. Script usage assumes Linux/Mac OS X parent host system. 
* git client to checkout this repository
* If one want to generate more data or change queries one need python3 with numpy installed
* Ensure you have enough memory available. The Vespa container needs about 5GB and the Elastic container is configured with 8GB heap so 10GB should be about sufficient. 

## Instructions to reproduce benchmark
Clone, build containers and run. Note that the repository contains data and feed files for 60K queries and is about 1.2GB..
<pre>
$ git clone https://github.com/jobergum/dense-vector-ranking-performance.git; cd dense-vector-ranking-performance
$ ./bin/build.sh 
$ ./bin/run-sh
</pre>

Verify that the two docker containers are running:
<pre>
$ docker ps |egrep "vespa|es"
</pre>

### Deploy configuration and document schema 
**Vespa**
Verify that configuration service is running and returns 200 OK:
<pre>
$ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
</pre>
<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare config && \
    /opt/vespa/bin/vespa-deploy activate'
</pre>

**Elastic**
Verify that elastic service is running and returns 200 OK:
<pre>
$ docker exec es bash -c 'curl -s --head http://localhost:9200/'
</pre>
Deploy Elastic index schema 
<pre>
$ docker exec es bash -c '/usr/share/elasticsearch/create-index.sh'
</pre>

### Feed data
This takes about 8 minutes with Vespa and about 36 minutes with Elastic. The python feed script simply
posts documents one at a time in one thread. Both Vespa and Elastic has batch feed api's with higher performance but
to keep the dependency list short we opt to use the simplistic HTTP apis. 
<pre>
$ time docker exec es bash -c 'python feed.py'
$ time docker exec vespa bash -c 'python feed.py'
</pre>

### Run benchmark 
<pre>
$ ./bin/do-benchmark.sh 
</pre>
