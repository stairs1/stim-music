#!/usr/bin/env bash

#install ffmpeg: sudo apt-get install ffmpeg

input=$1
filename=$(basename -- "$input")
filename="${filename%.*}"

ffmpeg -i $input "$filename".wav
