#!/bin/sh
echo "Elastic 7.4 Vector Similarity Search"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa -P -H "Content-Type:application/json" -q /tmp/queries/elastic/queries.txt -s 120 -n 1 -c 0 -i 20 -o /tmp/queries/result.es.txt localhost 9200 

echo "Vespa Vector Similarity Search"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa -P -H "Content-Type:application/json" -q /tmp/queries/vespa/queries.txt -s 120 -n 1 -c 0 -i 20 -o /tmp/queries/result.vespa.txt localhost 8080 

