#!/bin/bash

num_runs=100
delay_seconds=1

for (( i=1; i<=$num_runs; i++ ))
do
    echo "Running tests, iteration $i"
    python manage.py test

    if [ $? -ne 0 ]; then
        echo "There were test failures, stopping the loop"
        break
    fi

    echo "Waiting for $delay_seconds seconds before running tests again"
    sleep $delay_seconds
done

