#!/bin/sh

search_dir=/storage/Library/Sorted
outputfile=stats.txt

#generate logs 
journalctl --user -u audio-scheduler --no-tail > audiosched_log.txt
#for specific dates:
#journalctl --user -u audio-scheduler -S "2022-09-16 00:00:00" --no-tail > audiosched_log.txt

#remove some lines
grep -v "Could not stat(/storage/Library/Sorted/" audiosched_log.txt > tmpfile && mv tmpfile audiosched_log.txt
grep -v "No such file or directory" audiosched_log.txt > tmpfile && mv tmpfile audiosched_log.txt
grep -v "Not a regular file" audiosched_log.txt > tmpfile && mv tmpfile audiosched_log.txt

for entry in "$search_dir"/*
do
count=$(grep -nrc "$entry" audiosched_log.txt) 
echo "$entry" "}" "$count" >> $outputfile

done

#sort output ascending order (ignore a*s*y*s and classical, various,etc)
sort -n -t '}' -k 2 stats.txt > stats_sorted.txt
