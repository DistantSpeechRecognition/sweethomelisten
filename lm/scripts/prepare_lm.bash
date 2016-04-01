PROMPTS=AllEnet-LM.lc.prompts
PROMPTS_rev=AllEnet-LM.lc.clr
#REVERSED=AllEnet-LM.prompts.reversed
VOCAB=AllEnet-LM.words

#ngram-count -text $PROMPTS -order 3 -kndiscount -interpolate -write-vocab $VOCAB -lm logot_3.lm
#python find_prons.py Greek400k.dictionary found_words.list < AllEnet-LM.words > AllEnet.dico
#ngram-count -text $PROMPTS -order 3 -kndiscount -interpolate -limit-vocab -vocab found_words.list -lm logot_3.lm


#ngram-count -text $PROMPTS -order 2 -kndiscount -interpolate -limit-vocab -vocab found_words.list -lm logot_2.lm

echo $PROMPTS > lm_train.list
perl reverse.pl --fileList lm_train.list --dataDir ./ --outputDir ./
ngram-count -text ${PROMPTS_rev} -order 3 -kndiscount -interpolate -limit-vocab -vocab found_words.list -lm logot_3_rev.lm.1

mkbingram.dSYM -nlr logot_2.lm -nrl logot_3_rev.lm.1 -swap julius_logot.bin 
