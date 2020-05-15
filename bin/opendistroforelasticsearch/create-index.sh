#!/bin/sh
curl -s -X PUT "localhost:19200/doc?pretty" -H "Content-Type:application/json" -d @config/index.json 
