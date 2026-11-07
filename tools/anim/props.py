import numpy as np
def _frame(a):
    a=np.asarray(a,float); a/=np.linalg.norm(a); h=np.array([1.,0,0]) if abs(a[0])<0.9 else np.array([0,1.,0])
    e1=np.cross(h,a); e1/=np.linalg.norm(e1); e2=np.cross(a,e1); return e1,e2     # e1 x e2 = a
class Geo:
    def __init__(s): s.P=[];s.N=[];s.I=[];s.n=0
    def _add(s,P,N,I): s.P.append(np.asarray(P,float));s.N.append(np.asarray(N,float));s.I.append(np.asarray(I)+s.n);s.n+=len(P)
    def box(s,x0,x1,y0,y1,z0,z1):
        c=np.array([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]); h=np.array([(x1-x0)/2,(y1-y0)/2,(z1-z0)/2])
        for ax in range(3):
            for sg in (1,-1):
                n=np.zeros(3); n[ax]=sg; u=np.zeros(3); u[(ax+1)%3]=1; v=np.cross(n,u)
                if sg<0: u,v=v,u; v=np.cross(n,u)
                # guarantee u x v = n
                if np.dot(np.cross(u,v),n)<0: v=-v
                P=[c+n*h[ax]*1+(-u)*h[(ax+1)%3]+(-v)*abs(v@h)*1 if False else None]
                us=np.abs(u)@h; vs=np.abs(v)@h
                P=[c+n*h[ax]+su*u*us+sv*v*vs for su,sv in ((-1,-1),(1,-1),(1,1),(-1,1))]
                s._add(P,[n]*4,[0,1,2,0,2,3])
    def cyl(s,c,axis,r,length,seg=28,caps=True):
        a=np.asarray(axis,float); a/=np.linalg.norm(a); e1,e2=_frame(a); c=np.asarray(c,float)
        th=np.linspace(0,2*np.pi,seg,endpoint=False); rad=np.array([np.cos(t)*e1+np.sin(t)*e2 for t in th])
        bot=c-a*length/2+rad*r; top=c+a*length/2+rad*r
        P=np.vstack([bot,top]); N=np.vstack([rad,rad]); I=[]
        for i in range(seg):
            j=(i+1)%seg; I+=[i,j,seg+i, j,seg+j,seg+i]
        s._add(P,N,I)
        if caps:
            for sg,ring in ((1,top),(-1,bot)):
                ctr=c+a*sg*length/2; P=np.vstack([[ctr],ring]); N=np.tile(a*sg,(seg+1,1)); I=[]
                for i in range(seg):
                    j=(i+1)%seg; I+=([0,1+i,1+j] if sg>0 else [0,1+j,1+i])
                s._add(P,N,I)
    def arrays(s): return np.vstack(s.P).astype('<f4'),np.vstack(s.N).astype('<f4'),np.concatenate(s.I).astype('<u4')
