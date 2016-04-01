function [start,ent,output]= intervals(A,fs,td)

%find start and end times of activity
Ao= A;
ai= Ao > 0;
Ao(ai)= 1;
Ao= [0 Ao 0];
Adiff= diff(Ao);
ent= find(Adiff==-1);
ent= ent-1;
start= find(Adiff==1);

%delete gaps between intervals of the same event
lstart= length(start);
for i=1:lstart-1
    if (A(start(i)) == A(start(i+1))) && ((start(i+1)-ent(i)-1)/fs < td)
            A(ent(i):start(i+1))= A(start(i));
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