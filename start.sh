#!/bin/bash
printf "\n-- Deleting spark archive --\n"
rm spark/*.tgz
printf "\n-- Downloading spark archive --\n"
spark/get-spark.sh

# Optional:
# printf "\n-- Updating songs trainging set --\n"
# ./update_training_sets.sh

printf "\n-- Starting containers --\n"
docker-compose up -d
printf "\n-- Starting producer cli --\n"
./sproducer.sh
