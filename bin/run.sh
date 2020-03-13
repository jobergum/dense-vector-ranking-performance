#!/bin/sh
docker run  --privileged --name es -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e ES_JAVA_OPTS="-Xms8g -Xmx8g"  -d es_benchmark:1.1
docker run  --privileged --name vespa -p 8080:8080 -d vespa_benchmark:1.1
