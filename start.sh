#!/bin/bash
echo "Deleting spark archive"
rm spark/*.tgz
echo "Downloading spark archive"
spark/get-spark.sh

# Optional:
# echo "Updating songs trainging set"
# ./update_training_sets.sh

echo "Starting containers"
docker-compose up -d
echo ""
echo "After logstash initialization you can run sproducer.sh"
