grammar='../lm/demo_english/demo_commands_short.utts'

#while read line
##do
#	words=`echo $line | awk '{print NF}'`
#	echo $words
#	for i in $(seq 1 $words)
#	do
#		#echo $i		
#		gramw=`echo $line | awk '{printf("%s\n",$i)}'`
#		echo $gramw
#	done	
#done<$grammar

while read line
do
	currtoken=echo $line
	grep 

