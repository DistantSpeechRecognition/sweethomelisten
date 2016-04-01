basename=$1

python utts2gram.py < $basename.utts > $basename.gram
../../bin/linux_x86_64/HParse $basename.gram $basename.wdnet
