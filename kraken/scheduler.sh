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
                        log_file="${p}BNB.log"
                        python3 -u simple-rsi-stoch-loop.py "${p}" >> ${log_file} 2>&1 &
                fi
        done <coin.list
        while read p; do
                echo "$p"
                res=$(ps aux | grep "python3 -u simple-short" | grep "$p")
                if [ -z "$res" ]
                then
                        echo $p not running, will start now
                        log_file="${p}USDT.log"
                        python3 -u simple-short-bot.py "${p}" >> ${log_file} 2>&1 &
                fi
        done <short-coin.list
        sleep 30
done