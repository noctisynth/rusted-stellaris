"""Exercise Juggernaut/academy aura composition in a disposable RW 1.15 copy.

Temporarily disables combat and collision, checks normal binary stat records,
then restores configuration. This is not a combat balance or multiplayer test.
"""
from pathlib import Path
from argparse import ArgumentParser
from subprocess import Popen, CREATE_NO_WINDOW
from time import sleep, monotonic
from uuid import uuid4
from struct import pack, unpack
import re, socket, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from inspect_save_units import raw_save, unit_list

parser=ArgumentParser(description=__doc__)
parser.add_argument('--game-dir',required=True,type=Path)
game=parser.parse_args().game_dir.resolve()
if not game.is_relative_to((ROOT/'work').resolve()):parser.error('Use a disposable game copy inside work/')
mod=game/'mods/units/RustedStellarisDev'; units=mod/'units'
if not (units/'juggernaut.ini').is_file() or not (game/'jvm64/bin/java.exe').is_file():parser.error('Install the game runtime and current mod in the disposable copy')
run=ROOT/'work'/('juggernaut-aura-'+uuid4().hex[:8]);run.mkdir()
backups={}; extra=[]; proc=None
for path in units.glob('*.ini'):
    text=path.read_text(encoding='utf-8')
    if '[hiddenAction_academyTraining]' not in text: continue
    backups[path]=path.read_bytes()
    text=re.sub(r'^(?:radius|softCollisionOnAll):.*\n','',text,flags=re.M)
    text=text.replace('[core]\n','[core]\ncanNotBeDamaged: true\nradius: 0\nsoftCollisionOnAll: 0\n',1)
    if '[attack]' in text: text=text.replace('[attack]\n','[attack]\ncanAttack: false\n',1)
    else: text+='\n[attack]\ncanAttack: false\n'
    text=re.sub(r'^moveSpeed:.*$', 'moveSpeed: 0', text, flags=re.M)
    if '[movement]' not in text: text+='\n[movement]\nmoveSpeed: 0\n'
    if path.name=='juggernaut.ini':
        text=re.sub(r'^canBuild_.*\n','',text,flags=re.M)
        text=re.sub(r'\[canBuild_[^]]+\]\n(?:(?!\n\[).)*', '', text, flags=re.S)
        text+='''
[hiddenAction_probeLeaveAura]
autoTrigger: if self.globalTeamTags(includes='rsAuraLeave') and not self.hasFlag(id=5)
addResources: setFlag=5
teleportTo: self.getOffsetAbsolute(x=0,y=-850)

[hiddenAction_probeReturnAura]
autoTrigger: if self.globalTeamTags(includes='rsAuraReturn') and self.hasFlag(id=5)
addResources: unsetFlag=5
removeGlobalTeamTags: rsAuraLeave, rsAuraReturn
teleportTo: self.getOffsetAbsolute(x=0,y=850)

[hiddenAction_probeKillAura]
autoTrigger: if self.globalTeamTags(includes='rsAuraKill')
setUnitStats: hp=-1
'''
    text=re.sub(r'(\[action_upgrade(?:CruiserT2|BattleshipT2|ParadoxTitan)\][\s\S]*?buildSpeed:) [^\n]+',r'\1 1s',text)
    if path.name=='cruiser.ini':
        text+='''
[hiddenAction_probeUpgradeAura]
autoTrigger: if self.globalTeamTags(includes='rsAuraUpgrade') and self.maxHp==3680 and not self.hasFlag(id=6)
addResources: setFlag=6
alsoQueueAction: upgradeCruiserT2
'''
    path.write_text(text,encoding='utf-8')
academy=units/'fleet_academy.ini';backups[academy]=academy.read_bytes()
text=academy.read_text(encoding='utf-8').replace('buildSpeed: 60s','buildSpeed: 1s')
text+='''
[hiddenAction_probeTrain]
autoTriggerOnEvent: completeAndActive
addResources: credits=1000000, alloys=100000, science=100000
addGlobalTeamTags: rsTechShields
alsoQueueAction: trainFleet

[hiddenAction_probeRevoke]
autoTrigger: if self.globalTeamTags(includes='rsAuraRevokeAcademy')
deleteSelf: true
'''
academy.write_text(text,encoding='utf-8')
for phase,effect in {'Leave':'addGlobalTeamTags: rsAuraLeave','Return':'addGlobalTeamTags: rsAuraReturn','Kill':'addGlobalTeamTags: rsAuraKill','RevokeAcademy':'addGlobalTeamTags: rsAuraRevokeAcademy','Upgrade':'addGlobalTeamTags: rsAuraUpgrade'}.items():
    path=units/f'probe_aura_{phase.lower()}.ini';extra.append(path)
    path.write_text(f'[core]\ncopyFrom: _building_t2_common.ini\nname: rsAura{phase}Director\nprice: 0\nmaxHp: 1\n[hiddenAction_probe]\nautoTriggerOnEvent: completeAndActive\n{effect}\n[graphics]\nimage: fleet_academy.png\n',encoding='utf-8')
script=run/'start.debug';target='/SD/mods/units/RustedStellarisDev/[p2]Twin_Chokepoints.tmx'
script.write_text(f"root.open('levelOptions.rml','{target}')\nroot.loadConfigAndStartNew('{target}')\n",encoding='utf-8')
with socket.socket() as sock: sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
def send(code):
    with socket.create_connection(('127.0.0.1',port),timeout=5) as sock:
        sock.settimeout(15);sock.sendall(('script '+code+'\n').encode());reply=sock.recv(2048)
        if reply.strip()!=b'done':raise RuntimeError(reply)
def create(name,x,y,team):send(f"debug.createUnit('{name}',{x},{y},{team},false)")
def count_pair(raw,value,default=1.):
    if value==1/1.1:value=1/unpack('>f',pack('>f',1.1))[0]
    value=unpack('>f',pack('>f',value))[0]
    return raw.count(pack('>dd',value,default))
def save(label):
    sleep(2);name=run.name+'-'+label;send(f"root.saveGame('{name}')");sleep(.5)
    raw=raw_save(game/'saves'/(name+'.rwsave'));names=unit_list(raw)[0]
    counts={key:count_pair(raw,value) for key,value in [('damage10',1.1),('damage21',1.21),('delay',1/1.1)]}
    print(label,counts,flush=True);return raw,names,counts,name
args=[str(game/'jvm64/bin/java.exe'),'-Xmx1000M','-Dfile.encoding=UTF-8','-Djava.library.path=.','-cp','game-lib.jar;libs/*','com.corrodinggames.rts.java.Main','-width','800','-height','600','-debug',f'{port}:aura','-debugscript',str(script.resolve())]
try:
    with (run/'stdout.log').open('wb') as out,(run/'stderr.log').open('wb') as err:
        proc=Popen(args,cwd=game,stdout=out,stderr=err,creationflags=CREATE_NO_WINDOW)
        deadline=monotonic()+40
        while monotonic()<deadline:
            log=(run/'stdout.log').read_text(encoding='utf-8',errors='replace')
            if 'onGameCrash:' in log or proc.poll() is not None:raise RuntimeError('test startup failed: '+str(run))
            if 'selectAnyOnScreenBuilder: found builder' in log:break
            sleep(.25)
        sleep(2);send('debug.plainTextDebugSave(false)')
        send('debug.setTeamAllyGroup(0,0)');send('debug.setTeamAllyGroup(1,0)');send('debug.setTeamAllyGroup(2,2)')
        for name,x,y,team in [('rsCorvette',1300,900,0),('rsCruiser',1350,900,0),('rsBattleshipT2',1400,1000,0),('rsTitan',1300,1050,0),('rsFighter',1450,1050,0),('rsCorvette',2049,900,0),('rsCorvette',2051,900,0),('rsCorvette',1400,800,1),('rsCorvette',1400,850,2),('rsArk',1500,1000,0),('rsColossus',1550,1000,0)]:create(name,x,y,team)
        _,_,before,_=save('baseline');assert before['delay']==0
        create('rsJuggernaut',1400,900,1)
        _,_,first,_=save('ally-source');assert first['delay']>=7 and first['damage10']>=7,first
        create('rsJuggernaut',1400,900,0)
        _,_,second,_=save('two-sources');assert second==first,(first,second)
        create('rsFleetAcademy',100,1600,0)
        raw,_,trained,_=save('trained');assert trained['damage21']>=6 and trained['delay']==first['delay'],trained
        create('rsAuraUpgradeDirector',100,1650,0)
        raw,names,upgraded,name=save('upgraded');assert 'rsCruiserT2' in names and upgraded['damage21']>=6
        send(f"root.loadGame('{name}.rwsave')");send('root.resumeNonMenu()');send('debug.overrideDeltaSpeed(1)')
        _,_,loaded,_=save('reloaded');assert loaded==upgraded,(loaded,upgraded)
        create('rsAuraLeaveDirector',100,1500,0);create('rsAuraLeaveDirector',100,1500,1)
        _,_,outside,_=save('outside');assert outside['damage21']==0 and outside['delay']<first['delay'],outside
        create('rsAuraReturnDirector',100,1550,0);create('rsAuraReturnDirector',100,1550,1)
        _,_,returned,_=save('returned');assert returned==upgraded,(returned,upgraded)
        create('rsAuraRevokeAcademyDirector',100,1700,0)
        _,_,revoked,_=save('academy-lost');assert revoked['damage21']==0 and revoked['damage10']==first['damage10'] and revoked['delay']==first['delay'],revoked
        create('rsAuraKillDirector',100,1750,0);create('rsAuraKillDirector',100,1750,1)
        _,names,killed,name=save('sources-killed');assert killed['delay']==0 and killed['damage10']==0,killed
        send(f"root.loadGame('{name}.rwsave')");send('root.resumeNonMenu()');send('debug.overrideDeltaSpeed(1)')
        _,_,final,_=save('revoked-reloaded');assert final==killed
        print('PASS: ally aura, multiple-source cap, academy composition, upgrade, range withdrawal, destruction and binary save/load. '+str(run),flush=True)
finally:
    if proc is not None and proc.poll() is None:proc.terminate();proc.wait(timeout=5)
    for path,data in backups.items():path.write_bytes(data)
    for path in extra:path.unlink(missing_ok=True)
