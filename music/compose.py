"""Original instrumental game cues. Python stdlib synthesis; FFmpeg for MP3.
No third-party recordings, melodies, samples or generative service inputs.
Run from any directory. Intermediate WAVs are written to a supplied work folder.
"""
import argparse, array, json, math, random, subprocess, wave
from pathlib import Path
RATE=22050
TAU=math.tau
DEST=Path(__file__).resolve().parent
WORK=None
cache={}

def voice(kind,midi,duration):
    key=(kind,midi,round(duration,3))
    if key in cache:return cache[key]
    n=int((duration+(.8 if kind=='pluck' else .15))*RATE)
    freq=440*2**((midi-69)/12)
    rng=random.Random(midi*31+len(kind)*17+n)
    out=array.array('f',[0])*n
    if kind=='pluck':
        # Karplus-Strong string with soft pick attack and damped high harmonics.
        period=max(4,round(RATE/freq));ring=[rng.uniform(-1,1) for _ in range(period)]
        for i in range(n):
            j=i%period;value=ring[j];ring[j]=.4975*(ring[j]+ring[(j+1)%period])
            out[i]=value*min(1,i/(RATE*.006))*math.exp(-i/(RATE*1.5))
    else:
        phase=0
        for i in range(n):
            t=i/RATE;phase+=TAU*freq/RATE*(1+.0015*math.sin(TAU*4.7*t))
            env=min(1,t/.055)*min(1,max(0,(duration+.12-t)/.18))
            if kind=='flute':value=.72*math.sin(phase)+.12*math.sin(phase*2)+.025*rng.uniform(-1,1)
            elif kind=='pad':value=(math.sin(phase)+.4*math.sin(phase*1.003)+.13*math.sin(phase*2))*.45;env=min(1,t/.35)*min(1,max(0,(duration+.15-t)/.5))
            elif kind=='bass':value=.8*math.sin(phase)+.16*math.sin(phase*2);env=min(1,t/.012)*math.exp(-t/1.2)*min(1,max(0,(duration+.12-t)/.1))
            elif kind=='bell':value=.7*math.sin(phase)+.2*math.sin(phase*2.76)+.1*math.sin(phase*5.4);env=math.exp(-t*3)*min(1,t/.004)
            out[i]=value*env
    cache[key]=out;return out

def drum(kind):
    rng=random.Random(37+len(kind));length={'kick':.35,'snare':.21,'hat':.065,'shaker':.12}[kind]
    data=array.array('f',[0])*int(RATE*length);previous=0
    for i in range(len(data)):
        t=i/RATE;noise=rng.uniform(-1,1)
        if kind=='kick':v=math.sin(TAU*(47*t+8*(1-math.exp(-t*30))))*math.exp(-t*15)
        elif kind=='snare':v=(noise*.65+math.sin(TAU*170*t)*.3)*math.exp(-t*24)
        else:v=(noise-previous)*math.exp(-t*(80 if kind=='hat' else 38))*.35
        data[i]=v;previous=noise
    return data

def compose(name,bpm,bars,battle=False,profile=None):
    profile=profile or {}
    beat=60/bpm;bar=beat*4;length=bars*bar
    left=array.array('f',[0])*int((length+3)*RATE);right=array.array('f',[0])*len(left)
    def add(data,start,volume,pan=0,delay=True):
        index=int(start*RATE);l=volume*math.sqrt((1-pan)/2);r=volume*math.sqrt((1+pan)/2)
        echoes=[(0,1,l,r)]
        if delay:echoes += [(int(beat*.75*RATE),.15,r,l),(int(beat*1.5*RATE),.07,l,r)]
        for offset,gain,lg,rg in echoes:
            for j,value in enumerate(data):
                k=index+j+offset
                if 0<=k<len(left):left[k]+=value*gain*lg;right[k]+=value*gain*rg
    def note(kind,midi,start,duration,volume,pan=0):add(voice(kind,midi,duration),start,volume,pan)
    chords=[(52,[64,67,71]),(48,[60,64,67]),(55,[62,67,71]),(50,[62,66,69])]
    # Four related, original pentatonic phrases; leave breath between answers.
    phrases=[[(0,76,.75),(1,79,.5),(1.75,78,.5),(2.5,74,1)],[(.5,71,.5),(1.25,74,.5),(2,76,.75),(3,79,.6)],[(0,83,1),(1.5,81,.5),(2.25,79,.75),(3.25,76,.5)],[(0,74,.75),(1,71,.6),(2,74,.5),(3,76,.8)]]
    chords=profile.get('chords',chords)
    phrases=profile.get('phrases',phrases)
    arpeggio=profile.get('arpeggio',[0,1,2,1,0,2,1,2])
    drums={k:drum(k) for k in ['kick','snare','hat','shaker']}
    for b in range(bars):
        start=b*bar;section=b//8;root,chord=chords[(b//2)%len(chords)]
        intro=b<4;bridge=section==3 and not battle;outro=b>=bars-4
        note('pad',root+12,start,bar*1.1,.115 if not battle else .09,-.15)
        for idx,pitch in enumerate(chord):note('pad',pitch,start+.025*idx,bar*.95,.045,idx*.45-.45)
        for step in range(8):
            if (intro or (profile.get('sparse') and bridge)) and step%2:continue
            pitch=chord[arpeggio[(step+b%2)%8]]+(12 if step in [3,7] else 0)
            note('pluck',pitch,start+step*beat*.5,beat*.75,profile.get('pluckVolume',.24) if not bridge else .16,math.sin(step*.9)*.5)
        if not intro and not outro:
            phrase=phrases[(b//2+section)%len(phrases)]
            if b%2==0 or section in [1,4]:
                for off,pitch,dur in phrase:
                    note(profile.get('lead','flute') if not battle else 'pluck',pitch+(0 if section!=4 else -12),start+off*beat,beat*dur,profile.get('leadVolume',.14) if not battle else .32,.12)
            bell_every=profile.get('bellEvery',4)
            if b%bell_every==bell_every-1:note('bell',chord[2]+12,start+beat*3.5,beat*1.5,.07,-.5)
        for off in profile.get('bassBeats',([0,1.5,2.75] if battle else [0,2])):note('bass',root-12,start+off*beat,beat*.8,.19)
        if not bridge:
            for off in profile.get('kickBeats',([0,1.5,2.5] if battle else [0,2.5])):add(drums['kick'],start+off*beat,.28,0,False)
            if not intro:
                for off in [1,3]:add(drums['snare'],start+off*beat,.11 if not battle else .16,.1,False)
            for step in range(8 if not battle else 16):
                t=start+step*beat*(.5 if not battle else .25)+(beat*.025 if step%2 else 0)
                add(drums['shaker' if step%2 else 'hat'],t,.045 if step%2 else .065,(-.4 if step%2 else .4),False)
            if b%8==7:
                for step in range(4):add(drums['snare'],start+beat*(3+step*.25),.035+step*.016,(step-1.5)*.2,False)
        print(name,'bar',b+1,'/',bars,flush=True) if b%8==0 else None
    # Wrap release tails into the opening so the musical bar loop has no hard cut.
    count=int(length*RATE)
    for i in range(count,len(left)):left[i-count]+=left[i];right[i-count]+=right[i]
    peak=max(max(abs(x) for x in left[:count]),max(abs(x) for x in right[:count]));gain=.84/max(peak,.01)
    pcm=array.array('h')
    for i in range(count):pcm.append(round(max(-1,min(1,left[i]*gain))*32767));pcm.append(round(max(-1,min(1,right[i]*gain))*32767))
    wav=WORK/(name+'.wav')
    with wave.open(str(wav),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wav),'-af','highpass=f=35,lowpass=f=9000,loudnorm=I=-18:TP=-1.5:LRA=8','-ar','44100','-codec:a','libmp3lame','-b:a','160k',str(DEST/(name+'.mp3'))],check=True)
    print(name,'finished',round(length,2),'seconds',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workdir',nargs='?',default=str(DEST/'build'))
    parser.add_argument('--only',help='Comma-separated track stems to render; omit to render all six.')
    args=parser.parse_args();WORK=Path(args.workdir);WORK.mkdir(parents=True,exist_ok=True)
    profiles=json.loads((DEST/'stage-profiles.json').read_text(encoding='utf-8'))
    tracks={'moonlit-rooftops':{'bpm':100,'bars':40},'shadow-pulse':{'bpm':116,'bars':32,'battle':True},**profiles}
    requested=args.only.split(',') if args.only else list(tracks)
    unknown=set(requested)-set(tracks)
    if unknown:parser.error('Unknown tracks: '+', '.join(sorted(unknown)))
    for name in requested:
        config=tracks[name];compose(name,config['bpm'],config['bars'],config.get('battle',False),config)
        cache.clear()
