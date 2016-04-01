function [st,en,output]= intervals_expand(output,fs,td)

[st,en,output]= intervals(output,fs,0);

len= length(output);
for xx=1:length(st)
    interval= (st(xx):en(xx));
    output(max(1,interval(1)-td*fs):min(len,interval(length(interval))+td*fs))= 1;
end

end