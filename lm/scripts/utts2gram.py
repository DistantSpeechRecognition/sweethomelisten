#!/usr/bin/python
import sys
import re

utts=sys.stdin
grammar=sys.stdout

gram_string = "( SENT-START ( "
counter = 1
for ln in utts:
    if counter>1:
        gram_string += " | "
    ln = ln.rstrip("\r\n")
    print >> grammar, "$c{0} = {1};".format(counter, ln)
    gram_string += "$c{0}".format(counter)
    counter += 1

gram_string += " ) SENT-END )"
print >> grammar, gram_string




