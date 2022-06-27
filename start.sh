#!/bin/bash

first_argument="skip"

if [[ $1 = $first_argument ]]; then
    printf "\n-- Skipping downloading spark archive --\n"
else
    printf "\n-- Deleting spark archive --\n"
    rm spark/*.tgz
    printf "\n-- Downloading spark archive --\n"
    spark/get-spark.sh
fi


# Optional:
# printf "\n-- Updating songs trainging set --\n"
# ./update_training_sets.sh

printf "\n-- Starting containers --\n"
docker-compose up -d