#!/bin/bash
#this script is suppose to run every 30seconds. The functions in this script change the priority of java
#(java because snap and wings use java to run the jobs) and gdal processes. When they exceed 7 processes
#and when they are inferior or equal to 7 processes their priority are changed, using the nice value.
#The following was added on crontab(using root): 
#* * * * * /home/coresyf/prioritymanager/prioritymanager.sh
#* * * * * ( sleep 30 ; /home/coresyf/prioritymanager/prioritymanager.sh )


#this function changes the priority of snap(java) processes when they exceed 7 processes
priority () {

    identifiers=$(pgrep $1) #shows all processes by id of this app
    count=$(pgrep -c $1) #get the number of processes running of an application
    iterator=0
    
    if [ "$count" -gt 6 ]
    then
        for n in $identifiers
        do
            if [ "$iterator" -gt 6 ]
            then
                renice -n -12 -p $n
            fi
            iterator=$((iterator + 1))
            echo $iterator
        done
    else
        for n in $identifiers
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


priority java
priority gdal
