#!/bin/bash
#this script is suppose to run every minute. the functions in this script change the priority of snap and gdal processes
#when they exceed 15 and when they are inferior to 15 as well
#add the following on crontab: * * * * * for i in 0 1 2; do some_job & sleep 30; done; some_job
#with some_job being this script, in order to run every 30seconds


#this function changes the priority of snap processes when they exceed 15 processes
prioritySnap () {

    snapIds=$(pgrep java)
    gdalIds=$(pgrep gdal) #shows all processes by id of this app
    snapCount=$(pgrep -c java) 
    gdalCount=$(pgrep -c gdal) #get the number of processes running of an application
    iterator=0
    
    if [ "$snapCount" -gt 6 ]
    then
        for n in $snapIds
        do
            if [ "$iterator" -gt 6 ]
            then
                renice -n -12 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done
    else
        for n in $snapIds
        do
            if [ "$iterator" -le 6 ]
            then
                renice -n 0 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done    
    fi    
}

priorityGdal () {

    snapIds=$(pgrep snap)
    gdalIds=$(pgrep gdal) #shows all processes by id of this app
    snapCount=$(pgrep -c snap) 
    gdalCount=$(pgrep -c gdal) #get the number of processes running of an application
    iterator=0
    
    if [ "$snapCount" -gt 6 ]
    then
        for n in $snapIds
        do
            if [ "$iterator" -gt 6 ]
            then
                renice -n -12 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done
    else
        for n in $snapIds
        do
            if [ "$iterator" -le 6 ]
            then
                renice -n 0 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done    
    fi    
}


prioritySnap
priorityGdal
