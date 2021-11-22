#!/bin/bash

while true
do
	date
	while read p; do
		echo "$p"
		res=$(ps aux | grep python | grep "$p")
		if [ -z "$res" ]
		then
			echo $p not running, will start now
	      		python3 -u simple-sma-loop.py $p > $pUSD.log 2>&1 &	
		fi
		done <coin.list
	sleep 5
done
