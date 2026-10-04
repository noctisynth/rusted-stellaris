"""Reusable sampled-orchestra renderer for original instrumental cues.

VSCO 2 CE recordings (CC0) plus newly synthesized ambience and pulses.
This module does not open or incorporate any Stellaris audio.
"""
from pathlib import Path
from functools import lru_cache
import json, math, subprocess, wave
import numpy as np

from paths import WORK as ROOT, INSTRUMENTS
SR=32000
SUSTAIN={'cello','violin','viola','horn','flute','solo_violin'}
FILTERS={
 'horn':(95,4500),'cello':(48,5800),'violin':(145,6800),
 'viola':(95,6100),'solo_violin':(160,5600),'flute':(180,6700),
 'spiccato':(155,6500),'piano':(70,2900),'harp':(100,4600),
 'drum':(26,2300),'cymbal':(450,9000),
}

def filt(a,lo,hi):
    n=1<<(len(a)-1).bit_length()
    f=np.fft.rfftfreq(n,1/SR)
    curve=(1-np.exp(-(f/max(lo,1))**4))/(1+(f/hi)**6)
    return np.fft.irfft(np.fft.rfft(a,n,axis=0)*curve[:,None],n,axis=0)[:len(a)].astype(np.float32)

@lru_cache(None)
def load_sample(path,kind):
    b=subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/'samples'/path),
                      '-ar',str(SR),'-ac','2','-f','f32le','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(b,dtype='<f4').reshape(-1,2).copy()
    if kind not in ('drum','cymbal'):
        peak=np.max(np.abs(a),axis=1)
        active=np.flatnonzero(peak>max(peak.max()*.012,.00003))
        if len(active):a=a[max(0,active[0]-int(.015*SR)):]
    a=filt(a,*FILTERS[kind])
    if kind in SUSTAIN:
        mid=a[int(.25*SR):min(len(a),int(3*SR))]
        a*=.13/max(float(np.sqrt(np.mean(mid*mid))),.002)
    else:a*=.58/max(np.max(np.abs(a)),.001)
    return a

class Orchestra:
    def __init__(self,name,bpm,beats,seed=42,tail=8,room=1.0):
        self.name=name;self.bpm=bpm;self.beat=60/bpm
        self.length=beats*self.beat+tail;self.n=int(self.length*SR)
        self.dry=np.zeros((self.n,2),np.float32);self.send=np.zeros_like(self.dry)
        self.rng=np.random.default_rng(seed);self.events=[];self.room=room
        self.inst=json.loads(INSTRUMENTS.read_text(encoding='utf-8'))

    def put(self,a,seconds,gain=1,pan=0,wet=.4):
        start=max(0,int(seconds*SR));n=min(len(a),self.n-start)
        if n<=0:return
        a=a[:n].copy();mid=a.mean(axis=1);side=(a[:,0]-a[:,1])*.28
        a[:,0]=(mid+side)*math.sqrt(1-pan)*gain
        a[:,1]=(mid-side)*math.sqrt(1+pan)*gain
        self.dry[start:start+n]+=a;self.send[start:start+n]+=a*wet

    def play(self,kind,b,p,dur,gain,pan=0,vel=50,wet=.4):
        assert 0<=b and dur>0 and 0<=p<=127 and abs(pan)<=1
        options=self.inst[kind]
        valid=[r for r in options if r.get('lovel',0)<=vel<=r.get('hivel',127)]
        r=min(valid or options,key=lambda r:abs(r['root']-p))
        src=load_sample(r['path'],kind);rate=2**((p-r['root'])/12)
        seconds=dur*self.beat
        release=.85 if kind in SUSTAIN else 2.5
        if kind=='spiccato':release=.13
        count=int((seconds+release)*SR)
        pos=np.arange(count)*rate
        a=np.stack([np.interp(pos,np.arange(len(src)),src[:,i],left=0,right=0) for i in range(2)],axis=1).astype(np.float32)
        if kind in SUSTAIN and pos[-1]>len(src)*.88:
            natural=int(len(src)/rate);first=int(min(1.1*SR,natural*.22));last=int(min(4.6*SR,natural*.73))
            cross=min(int(.28*SR),(last-first)//3);write=last
            while write<count-cross:
                take=min(last-first,count-(write-cross))
                seg=a[first:first+take].copy();blend=min(cross,take)
                w=np.linspace(0,1,blend,dtype=np.float32)[:,None]
                a[write-cross:write-cross+blend]=a[write-cross:write-cross+blend]*(1-w)+seg[:blend]*w
                a[write-cross+blend:write-cross+take]=seg[blend:]
                write+=take-cross
                if take<=cross:break
        t=np.arange(count)/SR
        attack={'horn':.085,'cello':.12,'violin':.2,'viola':.18,'solo_violin':.14,
                'flute':.08,'spiccato':.004,'piano':.016,'harp':.006,'drum':.002,'cymbal':.015}[kind]
        env=np.minimum(t/attack,1)*np.clip((seconds+release-t)/release,0,1)**1.6
        if kind in SUSTAIN:env*=.78+.22*np.sin(np.minimum(t/max(seconds,.1),1)*np.pi)
        a*=env[:,None]
        timing=self.rng.uniform(-.012,.015) if kind not in ('drum','cymbal') else 0
        self.put(a,max(0,b*self.beat+timing),gain,pan,wet)
        self.events.append({'kind':kind,'beat':b,'pitch':p,'duration':dur,'gain':gain})

    def pad(self,b,dur,notes,gain=.025,airy=False):
        n=int((dur*self.beat+2.5)*SR);t=np.arange(n)/SR
        a=np.zeros((n,2),np.float32)
        for k,p in enumerate(notes):
            f=440*2**((p-69)/12)
            for channel in range(2):
                phase=self.rng.uniform(0,6.28)
                for detune in (-.0017,.0013):
                    z=2*np.pi*f*(1+detune*(1 if channel==0 else -1))*t+phase
                    sig=np.sin(z)+.18*np.sin(2*z+.1*np.sin(t*.7))+.06*np.sin(3*z)
                    a[:,channel]+=(sig*(.8+.2*np.sin(t*.37+k))*.5).astype(np.float32)
        env=np.minimum(t/(2.7 if airy else 1.8),1)*np.clip((n/SR-t)/2.5,0,1)
        a*=env[:,None]*gain/len(notes)
        self.put(a,b*self.beat,wet=.78 if airy else .55)

    def pluck(self,b,p,gain=.025,dur=1.1,pan=0):
        n=int(dur*SR);t=np.arange(n)/SR;f=440*2**((p-69)/12)
        a=np.zeros((n,2),np.float32)
        for channel in range(2):
            for h in range(1,7):
                z=2*np.pi*f*h*(1+(-1 if channel else 1)*.0007)*t
                a[:,channel]+=(np.sin(z)*np.exp(-t*(3.2+h*1.4))/h**1.4).astype(np.float32)
        env=np.minimum(t/.008,1)*np.clip((dur-t)/.12,0,1)
        a*=env[:,None]*gain
        self.put(a,b*self.beat,pan=pan,wet=.38)
        self.put(a,(b+.75)*self.beat,gain=.17,pan=-pan,wet=.6)
        self.events.append({'kind':'synth_pluck','beat':b,'pitch':p,'duration':dur/self.beat,'gain':gain})

    def bass_pulse(self,b,p,gain=.035):
        n=int(.42*SR);t=np.arange(n)/SR;f=440*2**((p-69)/12)
        sig=(np.sin(2*np.pi*f*t)+.16*np.sin(4*np.pi*f*t))*np.exp(-t*9)*np.minimum(t/.009,1)
        self.put(np.stack([sig,sig],axis=1).astype(np.float32),b*self.beat,gain,0,.14)

    def dust(self,b,gain=.008):
        n=int(.13*SR);t=np.arange(n)/SR;noise=self.rng.standard_normal(n)
        noise=noise-np.convolve(noise,np.ones(13)/13,mode='same')
        noise*=np.exp(-t*42)*np.minimum(t/.005,1)
        a=np.stack([noise,np.roll(noise,17)],axis=1).astype(np.float32)
        self.put(a,b*self.beat,gain,.3,.12)

    def swell(self,b,gain=.035):
        src=load_sample(self.inst['cymbal'][0]['path'],'cymbal')[:int(2.5*SR)]
        reverse=src[::-1].copy()*np.linspace(0,1,len(src))[:,None]**1.6
        self.put(reverse,max(0,b*self.beat-2.5),gain,-.12,.7)
        self.play('cymbal',b,60,2,gain*.8,-.1,wet=.65)

    def finish(self):
        print(self.name,'mixing',len(self.events),'notes',flush=True)
        mix=self.dry.copy()
        for channel in range(2):
            size=int((4.7*self.room)*SR);t=np.arange(size)/SR
            noise=self.rng.standard_normal(size)
            tail=np.convolve(noise,np.ones(9)/9,mode='same')
            ir=(tail*np.exp(-t*(1.7/self.room))*np.minimum(t/.11,1)).astype(np.float32)
            ir[:int(.036*SR)]=0
            ir*=.9/max(np.sqrt(np.sum(ir*ir)),1e-9)
            for sec,gain in [(.043,.22),(.071,.16),(.103,.11),(.149,.075)]:
                ir[int((sec+channel*.004)*SR)]+=gain
            fftsize=1<<(self.n+len(ir)-2).bit_length()
            wet=np.fft.irfft(np.fft.rfft(self.send[:,channel],fftsize)*np.fft.rfft(ir,fftsize),fftsize)[:self.n]
            mix[:,channel]+=wet*.52
        mix=filt(mix,27,11500)
        fade=np.minimum(np.arange(self.n)/(1.5*SR),1)*np.minimum((self.n-np.arange(self.n))/(4.5*SR),1)
        mix*=fade[:,None]
        assert np.all(np.isfinite(mix))
        mix*=.79/max(float(np.max(np.abs(mix))),.001)
        path=ROOT/(self.name+'_mix.wav')
        with wave.open(str(path),'wb') as f:
            f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
            f.writeframes((mix*32767).astype('<i2').tobytes())
        (ROOT/(self.name+'_events.json')).write_text(json.dumps({'bpm':self.bpm,'duration':self.length,'events':self.events},indent=2),encoding='utf-8')
        print('Saved',path.name,round(self.length,2),'seconds',flush=True)
        return path
