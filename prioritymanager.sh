#!/bin/bash
#this script is suppose to run every 30seconds. The functions in this script change the priority of java
#(java because snap and wings use java to run the jobs) and gdal processes. When they exceed 7 processes
#and when they are inferior or equal to 7 processes their priority are changed, using the nice value.
#The following was added on crontab(using root): 
#* * * * * /home/coresyf/prioritymanager/prioritymanager.sh
#* * * * * ( sleep 30 ; /home/coresyf/prioritymanager/prioritymanager.sh )


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
    
    if [ "$gdalCount" -gt 6 ]
    then
        for n in $gdalIds
        do
            if [ "$iterator" -gt 6 ]
            then
                renice -n -12 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done
    else
        for n in $gdalIds
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
