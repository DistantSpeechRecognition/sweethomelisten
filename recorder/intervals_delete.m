function [start,ent,output]= intervals_delete(A,fs,td)

%find start and end times of activity
Ao= A;
ai= Ao > 0;
Ao(ai)= 1;
Ao= [0 Ao 0];
Adiff= diff(Ao);
ent= find(Adiff==-1);
ent= ent-1;
start= find(Adiff==1);

%delete intervals with small duration (<td)
lstart= length(start);
for i=1:lstart
    if (ent(i)-start(i))/fs < td
            A(start(i):ent(i))= 0;
    end
end
output= A;

Ao= A;
ai= Ao > 0;
Ao(ai)= 1;
Ao= [0 Ao 0];
Adiff= diff(Ao);
ent= find(Adiff==-1);
ent= ent-1;
start= find(Adiff==1);
end