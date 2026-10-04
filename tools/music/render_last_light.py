"""Last Light / 最后的星光 — original sampled orchestral space cue.

No Stellaris audio is used in this render. Instruments: VSCO 2 CE, CC0.
Run through tools/build_music.py to fetch and verify the pinned CC0 samples.
"""
from pathlib import Path
from functools import lru_cache
import json, subprocess, wave, math, struct
import numpy as np

from paths import WORK as ROOT, INSTRUMENTS
SR=32000
BPM=72
BEAT=60/BPM
BAR=BEAT*4
LENGTH=32*BAR+8
N=int(LENGTH*SR)
RNG=np.random.default_rng(271828)
INST=json.loads(INSTRUMENTS.read_text(encoding='utf-8'))
dry=np.zeros((N,2),np.float32)
send=np.zeros_like(dry)
events=[]

def spectral_filter(audio,lo=35,hi=8000):
    size=1<<(len(audio)-1).bit_length()
    frequencies=np.fft.rfftfreq(size,1/SR)
    curve=(1-np.exp(-(frequencies/max(lo,1))**4))/(1+(frequencies/hi)**6)
    spec=np.fft.rfft(audio,n=size,axis=0)
    return np.fft.irfft(spec*curve[:,None],n=size,axis=0)[:len(audio)].astype(np.float32)

@lru_cache(None)
def sample(path,kind):
    result=subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/'samples'/path),
                           '-ar',str(SR),'-ac','2','-f','f32le','-'],capture_output=True,check=True)
    a=np.frombuffer(result.stdout,dtype='<f4').reshape(-1,2).copy()
    if kind not in ('drum','cymbal'):
        # Remove recording lead-in; retain the natural bow and breath attack.
        sm=np.max(np.abs(a),axis=1)
        onset=np.where(sm>max(sm.max()*.012,.00003))[0]
        if len(onset):a=a[max(0,onset[0]-int(.015*SR)):]
    lo={'horn':95,'cello':48,'violin':145,'piano':70,'harp':100,'drum':26,'cymbal':450}[kind]
    hi={'horn':4500,'cello':5800,'violin':6800,'piano':2400,'harp':4500,'drum':2300,'cymbal':9000}[kind]
    a=spectral_filter(a,lo,hi)
    if kind in ('drum','cymbal','piano','harp'):
        a*=.58/max(np.max(np.abs(a)),.001)
    else:
        s=a[int(.25*SR):min(len(a),int(3*SR))]
        a*=.13/max(float(np.sqrt(np.mean(s*s))),.002)
    return a

def place(a,time,pan,gain,wet=.36):
    start=max(0,int(time*SR)); count=min(len(a),N-start)
    if count<=0:return
    a=a[:count].copy()
    # Preserve sample stereo, with a narrowed stage position for each section.
    mid=(a[:,0]+a[:,1])*.5;side=(a[:,0]-a[:,1])*.28
    a[:,0]=(mid+side)*math.sqrt(1-pan)*gain
    a[:,1]=(mid-side)*math.sqrt(1+pan)*gain
    dry[start:start+count]+=a
    send[start:start+count]+=a*wet

def play(kind,beat,pitch,duration,gain,pan=0,velocity=50,wet=.4):
    options=INST[kind]
    eligible=[r for r in options if r.get('lovel',0)<=velocity<=r.get('hivel',127)]
    region=min(eligible or options,key=lambda r:abs(r['root']-pitch))
    source=sample(region['path'],kind)
    rate=2**((pitch-region['root'])/12)
    seconds=duration*BEAT
    release=.9 if kind in ('violin','cello') else .65
    if kind in ('harp','piano'):release=2.6
    if kind in ('drum','cymbal'):release=3.0
    count=int((seconds+release)*SR)
    positions=np.arange(count,dtype=np.float64)*rate
    a=np.stack([np.interp(positions,np.arange(len(source)),source[:,i],left=0,right=0) for i in range(2)],axis=1).astype(np.float32)
    # Extend sustained notes only when the original recording would run out.
    if kind in ('horn','violin','cello') and positions[-1]>len(source)*.88:
        natural_len=int(len(source)/rate)
        loop_start=int(min(1.1*SR,natural_len*.22))
        loop_end=int(min(4.6*SR,natural_len*.73))
        cross=int(.28*SR)
        pos=loop_end
        while pos<count-cross:
            take=min(loop_end-loop_start,count-(pos-cross))
            segment=a[loop_start:loop_start+take].copy()
            blend=min(cross,take)
            w=np.linspace(0,1,blend,dtype=np.float32)[:,None]
            a[pos-cross:pos-cross+blend]=a[pos-cross:pos-cross+blend]*(1-w)+segment[:blend]*w
            a[pos-cross+blend:pos-cross+take]=segment[blend:]
            pos+=take-cross
            if take<=cross:break
    t=np.arange(count)/SR
    attack={'horn':.09,'cello':.12,'violin':.22,'piano':.016,'harp':.006,'drum':.002,'cymbal':.015}[kind]
    env=np.minimum(t/attack,1)*np.clip((seconds+release-t)/release,0,1)**1.6
    if kind in ('cello','violin','horn'):
        env*=.77+.23*np.sin(np.minimum(t/max(seconds,.1),1)*np.pi)
    a*=env[:,None]
    human=RNG.uniform(-.016,.018) if kind not in ('drum','cymbal') else 0
    place(a,beat*BEAT+human,pan,gain,wet)
    events.append({'instrument':kind,'beat':beat,'note':pitch,'duration':duration,'gain':gain})

def synth_pad(beat,duration,notes,level):
    count=int((duration*BEAT+2)*SR)
    t=np.arange(count)/SR
    a=np.zeros((count,2),np.float32)
    for k,midi in enumerate(notes):
        f=440*2**((midi-69)/12)
        for channel in range(2):
            ph=RNG.uniform(0,6.28)
            for detune in (-.0017,.0013):
                # Airy, evolving string-like bed, below the real instruments.
                phase=2*np.pi*f*(1+detune*(1 if channel==0 else -1))*t+ph
                sig=np.sin(phase)+.22*np.sin(2*phase+.1*np.sin(t*.7))+.08*np.sin(3*phase)
                a[:,channel]+=(sig*(.8+.2*np.sin(t*.43+k))*.5).astype(np.float32)
    envelope=np.minimum(t/2.1,1)*np.clip((count/SR-t)/2.2,0,1)
    a*=envelope[:,None]*level/max(1,len(notes))
    place(a,beat*BEAT,0,1,.65)

# Two-bar phrases; shared tones and inversions keep the harmony connected.
# bass, cello support, inner strings, upper strings, airy upper extension
H=[
 (38,50,57,65,76), # Dm(add9)
 (38,50,58,65,69), # Bbmaj7/D
 (38,50,58,67,69), # Gm9/D
 (33,45,57,64,74), # Dsus2/A
 (38,50,57,65,76),
 (34,46,57,62,76), # Bbmaj7(#11)
 (33,48,57,64,79), # Fmaj9/A
 (31,48,55,62,76), # Csus2/G
 (38,50,57,65,76),
 (34,46,57,62,77),
 (31,43,58,65,81), # Gm9
 (33,45,55,62,76), # A7sus4
 (34,46,57,62,76),
 (33,48,57,64,79),
 (31,43,58,64,74), # Gm6
 (38,50,57,65,76),
]
print('Rendering orchestra...',flush=True)
for phrase,(bass,cello,inner,upper,air) in enumerate(H):
    b=phrase*8
    swell=[.38,.43,.50,.52,.64,.66,.70,.72,.9,1,.96,.95,.73,.56,.40,.27][phrase]
    synth_pad(b,8,[bass+12,inner,air],.042*swell)
    # Actual low strings, quietly octave-reinforced rather than a loud sine bass.
    play('cello',b,bass,7.65,.14*swell,.22,wet=.38)
    if phrase>0:play('cello',b+.07,cello,7.65,.10*swell,.27,wet=.4)
    if phrase>=2:
        play('violin',b+.08,inner,7.7,.085*swell,-.23,velocity=45,wet=.46)
        play('violin',b+.12,upper,7.7,.09*swell,-.38,velocity=45 if phrase<8 else 75,wet=.46)
    if 8<=phrase<=11:
        play('violin',b+.14,air,7.6,.065*swell,-.17,velocity=73,wet=.5)

# An original theme: rising fourth, a restrained semitone turn, falling answer.
# Each phrase has a breath; long notes are supported by moving inner voices.
theme=[
 (16,57,1.5),(18,62,3),(21.5,64,.5),(22,65,1.7),
 (24,64,2),(26,62,2.7),(29,58,1.5),(31,57,.7),
 (32,57,1.5),(34,62,3),(37.5,64,.5),(38,65,1.7),
 (40,69,2.7),(43,67,.7),(44,65,2.7),(47,64,.6),
 (48,65,3),(51.5,64,.5),(52,60,2.8),(55,57,.7),
 (56,62,2.7),(59,64,.8),(60,62,2.7),
 (64,69,1.5),(66,74,3),(69.5,76,.5),(70,77,1.7),
 (72,76,2),(74,74,2.7),(77,69,1.5),(79,67,.7),
 (80,70,2.7),(83,69,.8),(84,67,2.8),(87,65,.7),
 (88,64,3),(91.5,62,.5),(92,61,2.7),
 (96,62,3),(100,65,2.5),(103,64,.7),
 (104,60,3),(108,57,3),
 (112,58,3),(116,57,2),(118,55,1.5),
 (120,57,2),(122,62,5.5),
]
for beat,pitch,dur in theme:
    if beat<32:
        play('cello',beat,pitch,dur,.225,.12,wet=.40)
    elif beat<64:
        play('horn',beat,pitch,dur,.29,-.06,velocity=52,wet=.42)
    elif beat<96:
        play('violin',beat,pitch,dur,.24,-.26,velocity=78,wet=.42)
        play('horn',beat+.025,pitch-12,dur,.23,.05,velocity=68,wet=.43)
    else:
        play('cello',beat,pitch,dur,.17,.15,wet=.50)

# Subtle answering line, only where the lead rests or holds.
for beat,pitch,dur in [(36,57,2.5),(44,58,2.5),(50,60,3),(58,55,3),
                        (68,65,3),(76,62,3),(84,58,3),(92,57,3)]:
    play('violin',beat,pitch+12,dur,.075,-.36,velocity=43,wet=.5)

# Quiet harp: irregular groups, no music-box lead or repetitive bell accents.
for phrase,h in enumerate(H):
    b=phrase*8
    if phrase in (0,15):pattern=[(0,h[1]+12),(3,h[2]+12),(6,h[3]+12)]
    elif phrase<4:pattern=[(0,h[1]+12),(2.5,h[2]+12),(5,h[3]+12)]
    elif phrase<12:pattern=[(0,h[1]+12),(1.5,h[2]+12),(3,h[3]+12),(4,h[1]+12),(5.5,h[2]+12),(7,h[4])]
    else:pattern=[(0,h[1]+12),(3,h[2]+12),(6,h[3]+12)]
    for j,(offset,pitch) in enumerate(pattern):
        play('harp',b+offset,pitch,1.3,.047*(1 if j%3==0 else .74),.34,wet=.62)
    if phrase in (0,2,4,6,12,14,15):
        for j,pitch in enumerate([h[1],h[2],h[3]]):
            play('piano',b+j*.05,pitch,4,.045,-.1,wet=.62)

# A low bowed pulse grows into the climax, with restrained orchestral drums.
for bar in range(8,24):
    h=H[bar//2]
    amp=.042 if bar<16 else .059
    for beat,pitch in [(0,h[1]),(1.5,h[2]-12),(2.5,h[1]),(3.5,h[2]-12)]:
        play('cello',bar*4+beat,pitch,.48,amp,.18,wet=.3)
for beat,gain in [(32,.09),(48,.12),(64,.19),(72,.11),(80,.16),(88,.12),(96,.11)]:
    play('drum',beat,36,.6,gain,.05,wet=.6)
for beat,gain in [(64,.055),(96,.03)]:
    play('cymbal',beat,60,4,gain,-.1,wet=.7)
    cym=sample(INST['cymbal'][0]['path'],'cymbal')[:int(2.2*SR)][::-1].copy()
    cym*=np.linspace(0,1,len(cym))[:,None]**1.5
    place(cym,beat*BEAT-2.2,-.1,gain*.6,.7)

# The dominant changes its suspension to C# for the late cadence.
play('violin',92,61,3.3,.065,-.2,wet=.46)
play('horn',124,50,3.5,.075,.1,velocity=40,wet=.55)

print('Rendering concert-hall space...',flush=True)
def hall_ir(channel):
    size=int(4.9*SR);t=np.arange(size)/SR
    noise=RNG.standard_normal(size)
    # Dense, dark, decorrelated tail; separate early reflections retain clarity.
    smooth=np.convolve(noise,np.ones(9)/9,mode='same')
    env=np.exp(-t*1.65)*np.minimum(t/.11,1)
    impulse=(smooth*env).astype(np.float32)
    impulse[:int(.035*SR)]=0
    impulse*=.9/max(np.sqrt(np.sum(impulse*impulse)),1e-9)
    for seconds,amount in [(.043,.22),(.071,.16),(.103,.11),(.149,.075)]:
        impulse[int((seconds+channel*.004)*SR)]+=amount
    return impulse

mix=dry.copy()
for channel in range(2):
    impulse=hall_ir(channel)
    size=1<<(N+len(impulse)-2).bit_length()
    wet=np.fft.irfft(np.fft.rfft(send[:,channel],size)*np.fft.rfft(impulse,size),size)[:N]
    mix[:,channel]+=wet*.52

# Clear the lowest rumble, keep string sheen restrained, and allow natural dynamics.
mix=spectral_filter(mix,27,11500)
fade=np.minimum(np.arange(N)/(1.8*SR),1)*np.minimum((N-np.arange(N))/(5.0*SR),1)
mix*=fade[:,None]
peak=float(np.max(np.abs(mix)))
mix*=.89/max(peak,.001)
path=ROOT/'last_light_mix.wav'
with wave.open(str(path),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR)
    f.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
(ROOT/'composition_events.json').write_text(json.dumps({'bpm':BPM,'events':events},indent=2),encoding='utf-8')
print('Saved',path,'duration',round(LENGTH,2),'seconds; peak',peak,flush=True)
