#PASSING EXECUTION
#Example of a passing execution
./dummy_tool --input input --output output

#NON ZERO EXITCODE
#Example of a non zero exitcode execution
./dummy_tool --input input --output output --error true

#NON ENPTY STDERR 
#Example of a non empty stderr execution
./dummy_tool --input input --output output --errmsg stderrmsg

#NO OUPUT
#Example of an execution without output
./dummy_tool --input input --output void_output --noutput true

#EMPTY OUTPUT
#Exemple of an execution with an empty output
./dummy_tool --input input --output empty_output --empty_output true 
