#!/bin/bash
echo "Updating spark/top_songs.csv with latest songs"
python3 spark/update_spotify_training_dataset.py
echo "Done"
