#!/bin/bash

# usage
# ./scheduler.sh > scheduler.log 2>&1 &

while true
do
	date
	while read p; do
		echo "$p"
		res=$(ps aux | grep python | grep "$p")
		if [ -z "$res" ]
		then
			echo $p not running, will start now
			log_file="${p}USDT.log"
			python3 -u simple-sma-loop.py "${p}" > ${log_file} 2>&1 &
		fi
		done <coin.list
	sleep 30
done
