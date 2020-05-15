#!/bin/sh
docker run  --privileged --name es -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -e ES_JAVA_OPTS="-Xms8g -Xmx8g"  -d es_benchmark:1.1
docker run  --privileged --name oes -p 19200:19200 -p 19300:19300 -e "discovery.type=single-node" -e ES_JAVA_OPTS="-Xms16g -Xmx16g"  -d oes_benchmark:1.1
docker run  --privileged --name vespa -p 8080:8080 -d vespa_benchmark:1.1
