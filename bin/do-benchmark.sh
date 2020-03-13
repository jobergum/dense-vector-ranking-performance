#!/bin/sh
echo "Elastic NNS"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa \
-P -H "Content-Type:application/json" -q /tmp/queries/elastic/queries.txt -s 180  -n 1 -c 0 -i 20 -o /tmp/queries/result.es.txt localhost 9200 

echo "Vespa NNS"
docker run -v $(pwd)/data/:/tmp/queries --net=host --rm --entrypoint /opt/vespa/bin/vespa-fbench docker.io/vespaengine/vespa \
-P -H "Content-Type:application/json" -q /tmp/queries/vespa/queries_ann.txt -s 180 -n 1 -c 0 -i 20 -o /tmp/queries/result_ann.vespa.txt localhost 8080 

