#export PYTHONPATH=/usr/local/lib/python2.7/site-packages/
export EGS_ROOT=/home/antigoni/spitakimou/kaldi/egs/wsj/s5
export KALDI_ROOT=/home/antigoni/spitakimou/kaldi
export PATH=$KALDI_ROOT/src/bin:$EGS_ROOT/utils/:$KALDI_ROOT/src/gmmbin/:$EGS_ROOT/steps/:$KALDI_ROOT/src/featbin/:$PATH
python realTimeAudio.py
