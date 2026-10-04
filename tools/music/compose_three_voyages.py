"""Three new instrumental compositions with distinct rhythms and lead instruments."""
import sys
from orchestra import Orchestra

def luminous_departure():
    # Fast, open and forward-moving. 4/4 at 112; B minor opens into D major.
    o=Orchestra('luminous_departure',112,224,seed=1101,tail=7,room=.85)
    B=(35,[54,59,62,66,73]);G=(31,[55,59,62,66,69])
    D=(38,[54,57,62,66,76]);A=(33,[52,57,61,64,71])
    DF=(30,[54,57,62,66,76]);AC=(37,[52,57,61,64,71])
    E=(40,[52,55,59,66,74]);EM=(40,[56,59,64,66,71])
    harmony=[B,B,G,A, B,G,DF,A, E,G,D,A, B,G, D,AC,B,G, EM,G,D,A, D,AC,B,G,E,B]
    for phrase,(bass,ch) in enumerate(harmony):
        b=phrase*8
        level=.48 if phrase<4 else (.78 if phrase<12 else (.45 if phrase<14 else (1 if phrase<26 else .55)))
        o.pad(b,8,[bass+12,ch[1],ch[-1]],.032*level)
        o.play('cello',b,bass,7.6,.11*level,.22,wet=.32)
        if phrase>=2:
            for j,p in enumerate(ch[1:4]):
                o.play('violin' if j else 'viola',b+j*.04,p,7.5,.063*level,-.25-j*.1,vel=48,wet=.38)
        # An eight-note undulating figure, with a different closing note each bar.
        pitches=[ch[1]+12,ch[2]+12,ch[3]+12,ch[2]+12,ch[4],ch[3]+12,ch[2]+12,ch[3]+12]
        steps=range(16) if phrase not in (12,13,27) else range(0,16,2)
        for step in steps:
            gain=.027*level*(1 if step%4==0 else .69)
            o.pluck(b+step*.5,pitches[step%8],gain,.83,pan=(-.28 if step%2 else .24))
        if 4<=phrase<26 and phrase not in (12,13):
            for beat in (0,2,4,6):
                o.bass_pulse(b+beat,bass,.042*level)
            for beat in (1,3,5,7):o.dust(b+beat,.009*level)
            for j,beat in enumerate((0,1.5,2.5,4,5.5,6.5)):
                o.play('spiccato',b+beat,ch[1+(j%2)],.36,.055*level,-.35,vel=50,wet=.25)
        if phrase in (0,2,12,13,26,27):
            for j,p in enumerate(ch[1:4]):o.play('piano',b+j*.06,p,3,.065,-.1,wet=.5)

    # The short ascending theme has syncopated answers and changing cadences.
    phrases={
      4:[(0,66,1),(1.5,69,.5),(2,71,2.5),(5,73,1),(6.5,74,1)],
      5:[(0,74,2.5),(3,73,.7),(4,71,2),(6.5,69,1)],
      6:[(0,69,1.5),(2,66,1),(3.5,69,.5),(4,74,2.5),(7,76,.6)],
      7:[(0,73,3),(4,71,1.5),(6,69,1.5)],
      8:[(0,67,2),(2.5,69,.7),(4,71,3)],
      9:[(0,74,2.5),(3,73,.8),(4,71,3)],
     10:[(0,78,2),(2.5,76,1),(4,74,2.5),(7,73,.7)],
     11:[(0,71,2),(3,69,3.8)],
     14:[(0,74,1),(1.5,76,.5),(2,78,2.5),(5,76,1),(6.5,74,1)],
     15:[(0,73,3),(4,76,2),(6.5,73,1)],
     16:[(0,74,1.5),(2,73,1),(3.5,71,.5),(4,78,2.5),(7,76,.6)],
     17:[(0,74,3),(4,71,1.5),(6,69,1.5)],
     18:[(0,71,2),(2.5,73,1),(4,76,2.5),(7,78,.6)],
     19:[(0,79,2.5),(3,78,.8),(4,74,3)],
     20:[(0,78,2),(2.5,76,1),(4,74,2.5),(7,73,.7)],
     21:[(0,76,2),(3,73,3.8)],
     22:[(0,74,1),(1.5,76,.5),(2,78,2.5),(5,81,1),(6.5,78,1)],
     23:[(0,76,2.5),(3,73,.7),(4,71,2),(6.5,69,1)],
     24:[(0,74,1.5),(2,73,1),(3.5,71,.5),(4,66,2.5),(7,69,.6)],
     25:[(0,71,3),(4,69,1.5),(6,67,1.5)],
     26:[(0,66,3),(4,64,3)],
     27:[(0,62,2),(3,59,4)],
    }
    for phrase,notes in phrases.items():
        for offset,p,dur in notes:
            kind='violin' if phrase<26 else 'piano'
            gain=.21 if phrase<14 else .25
            if kind=='piano':gain=.12
            o.play(kind,phrase*8+offset,p,dur,gain,-.2,vel=75 if phrase>=14 else 50,wet=.37)
            if 14<=phrase<26:o.play('horn',phrase*8+offset+.035,p-12,dur,.125,.1,vel=52,wet=.38)
    for b in (32,64,112,144,176):
        o.play('drum',b,36,.6,.1,wet=.4)
    for b in (32,112,176):o.swell(b,.024)
    return o.finish()

def far_shore():
    # Broad six-eight journey. Quarter=76, two dotted-quarter pulses per bar.
    o=Orchestra('far_shore',76,144,seed=2202,tail=8,room=1.05)
    EM=(40,[52,59,64,67,74]);C=(36,[52,55,59,64,78])
    G=(35,[50,55,59,62,69]);D=(38,[50,57,62,66,76])
    AM=(33,[52,57,60,64,71]);BS=(35,[54,57,59,64,73])
    BM=(35,[54,57,59,63,73]);F=(42,[54,57,61,64,69])
    # Each chord spans two 6/8 bars. Middle section briefly moves toward G major.
    harmony=[EM,EM,C,G, EM,C,AM,BS, G,D,C,EM, AM,C,F,BM, EM,C,G,D, AM,BS,C,EM]
    levels=[.34,.42,.51,.56,.65,.69,.72,.74,.81,.84,.85,.87,.95,1,.94,.9,.9,.86,.8,.76,.66,.55,.42,.27]
    for phrase,(bass,ch) in enumerate(harmony):
        b=phrase*6;s=levels[phrase]
        o.pad(b,6,[bass+12,ch[1],ch[-1]],.035*s)
        o.play('cello',b,bass,5.7,.14*s,.22,wet=.42)
        o.play('viola',b+.05,ch[1],5.7,.08*s,-.12,wet=.46)
        if phrase>=2:
            o.play('violin',b+.08,ch[2],5.7,.073*s,-.3,wet=.47)
            o.play('violin',b+.12,ch[3],5.7,.08*s,-.42,vel=50 if phrase<12 else 73,wet=.48)
        if 8<=phrase<20:
            # A rolling accompaniment with a clear two-part six-eight accent.
            arp=[ch[0]+12,ch[1]+12,ch[2]+12,ch[3]+12,ch[2]+12,ch[1]+12]
            for step in range(12):
                o.play('harp',b+step*.5,arp[step%6],.55,.039*s*(1 if step%3==0 else .72),.36,wet=.5)
        else:
            for j,offset in enumerate((0,1.5,3,4.5)):
                o.play('harp',b+offset,ch[1+j%3]+12,1.2,.032*s,.35,wet=.62)
        if phrase in (0,2,20,22,23):
            for j,p in enumerate(ch[1:4]):o.play('piano',b+j*.055,p,3,.055,-.12,wet=.58)
        if 8<=phrase<20:
            for offset in (0,3):o.play('cello',b+offset,ch[0],.65,.057*s,.24,wet=.4)
        if phrase in (4,8,12,14,16,18,20):o.play('drum',b,36,.65,.085*s,wet=.58)

    # Long-breathed, arching original theme; no melody from the reference is copied.
    lines={
      2:[(0,59,1.4),(1.5,64,2.8),(4.5,67,1.1)],
      3:[(0,66,1.4),(1.5,62,2.8),(4.5,59,1.1)],
      4:[(0,64,2.8),(3,66,1.3),(4.5,67,1.1)],
      5:[(0,71,2.8),(3,69,1.3),(4.5,67,1.1)],
      6:[(0,64,2.6),(3,60,1.2),(4.5,62,1.1)],
      7:[(0,66,2.5),(3,64,1),(4.5,63,1.1)],
      8:[(0,67,2.8),(3,71,1.25),(4.5,74,1.1)],
      9:[(0,73,1.3),(1.5,74,1.3),(3,69,2.7)],
     10:[(0,71,2.7),(3,67,1.3),(4.5,64,1.1)],
     11:[(0,66,1.2),(1.5,67,1.3),(3,64,2.7)],
     12:[(0,76,2.7),(3,74,1.3),(4.5,72,1.1)],
     13:[(0,71,2.7),(3,74,1.3),(4.5,76,1.1)],
     14:[(0,73,2.7),(3,69,2.7)],
     15:[(0,75,2.7),(3,73,1.3),(4.5,71,1.1)],
     16:[(0,76,2.7),(3,78,1.3),(4.5,79,1.1)],
     17:[(0,78,1.3),(1.5,76,1.3),(3,74,2.7)],
     18:[(0,74,2.7),(3,71,1.3),(4.5,67,1.1)],
     19:[(0,69,2.7),(3,66,2.7)],
     20:[(0,64,2.7),(3,60,2.7)],
     21:[(0,63,2.7),(3,59,2.7)],
     22:[(0,64,2.7),(3,67,2.7)],
     23:[(0,66,1.3),(1.5,64,4.1)],
    }
    for phrase,notes in lines.items():
        for off,p,d in notes:
            if phrase<4:o.play('cello',phrase*6+off,p,d,.20,.15,wet=.46)
            elif phrase<12:o.play('horn',phrase*6+off,p,d,.265,.03,vel=53,wet=.44)
            elif phrase<20:
                o.play('violin',phrase*6+off,p,d,.245,-.27,vel=77,wet=.43)
                o.play('horn',phrase*6+off+.035,p-12,d,.17,.06,vel=65,wet=.46)
            else:o.play('solo_violin',phrase*6+off,p,d,.19,-.18,wet=.58)
    for b,p in [(27,59),(39,57),(51,62),(63,59),(75,64),(87,61),(99,64),(111,59)]:
        o.play('viola',b,p,2.7,.08,-.08,wet=.46)
    for b in (48,72,96):o.swell(b,.03)
    return o.finish()

def nebula_echoes():
    # Intimate, unhurried instrumental cantilena. A singing flute replaces any vocal role.
    o=Orchestra('nebula_echoes',62,128,seed=3303,tail=9,room=1.32)
    FM=(41,[53,60,65,68,72]);DB=(37,[53,56,60,65,72])
    AB=(39,[51,56,60,63,70]);EB=(39,[51,58,63,67,72])
    BB=(34,[53,58,61,65,72]);CS=(36,[55,58,60,65,74])
    C=(36,[55,58,60,64,74])
    harmony=[FM,DB,AB,EB, FM,DB,BB,CS, DB,AB,BB,C, FM,DB,EB,FM]
    levels=[.32,.39,.47,.50,.61,.65,.66,.68,.73,.80,.82,.72,.63,.50,.38,.25]
    for phrase,(bass,ch) in enumerate(harmony):
        b=phrase*8;s=levels[phrase]
        o.pad(b,8,[bass+12,ch[1],ch[-1]+12],.035*s,airy=True)
        o.play('cello',b,bass,7.7,.085*s,.24,wet=.56)
        if phrase>=2:
            o.play('viola',b+.11,ch[1],7.7,.054*s,-.12,wet=.60)
            o.play('violin',b+.17,ch[3],7.7,.049*s,-.37,vel=42,wet=.66)
        # A sparse felt-like piano figure leaves the lead free to breathe.
        piano=[(0,ch[0]),(.09,ch[2]),(2.5,ch[3]),(4,ch[1]),(4.08,ch[2]),(6.5,ch[-1])]
        for j,(off,p) in enumerate(piano):
            o.play('piano',b+off,p,2.2,.082*s*(1 if j%3 else 1.13),-.16,wet=.60)
        if phrase in (0,2,4,8,12,14):
            o.play('harp',b+3,ch[-1]+12,2.5,.026,.43,wet=.76)
        if 8<=phrase<12:
            o.play('violin',b+.19,ch[-1],7.6,.043,-.28,vel=43,wet=.65)

    # Free rests and unequal phrases create a vocal-like shape without voices.
    lines={
      2:[(.5,72,2.5),(3.5,70,1),(5,68,2.2)],
      3:[(0,67,3),(4,65,2),(6.5,63,1)],
      4:[(0,65,2.5),(3,68,1),(4.5,72,2.6)],
      5:[(.5,73,3),(4.5,72,1),(6,68,1.4)],
      6:[(0,70,3.5),(4.5,68,1),(6,65,1.4)],
      7:[(0,67,2.5),(3.5,65,1),(5.5,64,1.6)],
      8:[(0,77,3.5),(4.5,75,1),(6,73,1.4)],
      9:[(0,72,2.5),(3,70,1),(4.5,68,2.6)],
     10:[(.5,73,3),(4.5,72,1),(6,70,1.4)],
     11:[(0,72,3),(4,67,2.5)],
     12:[(0,68,3),(4,65,2.5)],
     13:[(.5,68,2),(3.5,65,2),(6,60,1.4)],
     14:[(0,63,3),(4,67,2.5)],
     15:[(0,65,5.5)],
    }
    for phrase,notes in lines.items():
        for off,p,d in notes:
            if phrase<8 or phrase>=12:
                o.play('flute',phrase*8+off,p,d,.19 if phrase<12 else .15,.08,vel=50,wet=.56)
            else:
                o.play('solo_violin',phrase*8+off,p,d,.205,-.2,vel=50,wet=.55)
                if phrase in (8,10):o.play('flute',phrase*8+off+.04,p-12,d,.065,.16,wet=.67)
    for b,p,d in [(38,60,1.5),(46,61,1.4),(54,58,1.5),(70,65,1.5),(78,63,1.4),(86,61,1.5),(102,60,1.5)]:
        o.play('solo_violin',b,p,d,.064,-.22,wet=.65)
    return o.finish()

if __name__=='__main__':
    choices={'light':luminous_departure,'shore':far_shore,'nebula':nebula_echoes}
    for name in sys.argv[1:] or choices:
        print('Composing',name,flush=True)
        choices[name]()
