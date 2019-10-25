#!/bin/sh
curl -X PUT "localhost:9200/doc?pretty" -H "Content-Type:application/json" -d @config/index.json 
