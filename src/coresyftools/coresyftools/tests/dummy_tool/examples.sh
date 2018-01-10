#Test ok
#A simple test of ok
./dummy_tool --input input --output output

#Test non ok
#A simple test of failure
./dummy_tool --input input --output output --error true

#A simple stderr test
#Test stderr message
./dummy_tool --input input --output output --errmsg "stderrmsg"