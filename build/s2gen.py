"""Build STAGE2 data (rounds 4+) from a PlayHQ advanced fixture export. Usage: python3 s2gen.py export.csv out.json"""
import csv,re,json,sys,datetime,collections
src=open('gen.py').read().split('\n'); ns={'re':re}; exec('\n'.join(src[3:19]),ns); clean,club=ns['clean'],ns['club']
AGES=["U19 Boys","U16/19 Girls","U16 Boys","U14 Boys","U14 Girls","U12 Boys","U12 Girls","U10 Boys"]
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig')))
# results reported outside the export (e.g. a grading workbook), applied to matching unplayed rows
EXTRA=json.load(open(sys.argv[4])) if len(sys.argv)>4 else []
def _apply_extra():
  for e in EXTRA:
    eh,ea=clean(e['h']),clean(e['a'])
    for r in rows:
      m=re.match(r'\w+day (U\d+(?:/\d+)? (?:Boys|Girls))',r['Grade'])
      if not m or m.group(1)!=e['age'] or r['Round']!='Round %d'%e['r'] or r['Bye']: continue
      if {clean(r['Home Team']),clean(r['Away Team'])}!={eh,ea}: continue
      if r['Game Status']=='Final': break
      hs,as_=(e['hs'],e['as']) if clean(r['Home Team'])==eh else (e['as'],e['hs'])
      r['Game Status']='Final';r['Home Team Score']=str(hs);r['Away Team Score']=str(as_)
      if e.get('ff'): r['Home Team Result'],r['Away Team Result']=('Won by forfeit','Lost by forfeit') if hs>as_ else ('Lost by forfeit','Won by forfeit')
      else: r['Home Team Result'],r['Away Team Result']=('Drew','Drew') if hs==as_ else (('Won','Lost') if hs>as_ else ('Lost','Won'))
      print('extra result',e['age'],e['r'],r['Home Team'],hs,as_,r['Away Team']);break
    else: print('NO MATCH',e)
def parse(g):
  m=re.match(r'(\w+day) (U\d+(?:/\d+)? (?:Boys|Girls))(?: (D\d))?$',g); return (m.group(1),m.group(2),m.group(3) or 'D1') if m else (None,None,None)
def rnum(s):
  m=re.match(r'Round (\d+)$',s); return int(m.group(1)) if m else None
def dfmt(s):
  d=datetime.datetime.strptime(s,'%d/%m/%Y');return d.strftime('%a %-d %b')
def tfmt(s):
  if not s: return ''
  h,m=map(int,s.split(':'));return f'{(h-1)%12+1}:{m:02d}{"am" if h<12 else "pm"}'
_apply_extra()
out={'asAt':None,'ages':{}}
latest=None
for r in rows:
  ts=r.get('Last Updated At') or ''
  m=re.match(r'(\d\d)/(\d\d)/(\d{4}) (\d\d:\d\d)',ts)
  if m:
    k=(m.group(3),m.group(2),m.group(1),m.group(4))
    if latest is None or k>latest: latest=k
if latest: out['asAt']=f'{latest[0]}-{latest[1]}-{latest[2]} {latest[3]}'
for age in AGES:
  R=[r for r in rows if parse(r['Grade'])[1]==age and (rnum(r['Round']) or 0)>=4]
  if not R: continue
  nights={}
  for r in R: nights.setdefault(parse(r['Grade'])[2],parse(r['Grade'])[0])
  byround=collections.defaultdict(list)
  for r in R: byround[rnum(r['Round'])].append(r)
  dates={n:dfmt(collections.Counter(x['Game Date'] for x in v if x['Game Date']).most_common(1)[0][0]) for n,v in byround.items() if any(x['Game Date'] for x in v)}
  played=[n for n,v in sorted(byround.items()) if all(x['Game Status']=='Final' for x in v if not x['Bye'])]
  nxt=next((n for n,v in sorted(byround.items()) if any(x['Game Status']!='Final' for x in v if not x['Bye'])),None)
  cur_round=nxt or (played[-1] if played else 4)
  divs=collections.defaultdict(list)
  for r in byround[cur_round]:
    d=parse(r['Grade'])[2]
    for k in ('Home Team','Away Team','Bye'):
      if r[k]: divs[d].append(clean(r[k]))
  games=[]
  for n in sorted(byround):
    for r in byround[n]:
      if r['Bye'] or r['Game Status']!='Final': continue
      d=parse(r['Grade'])[2];h,a=clean(r['Home Team']),clean(r['Away Team'])
      hr,ar=r['Home Team Result'],r['Away Team Result'];hs,as_=int(r['Home Team Score'] or 0),int(r['Away Team Score'] or 0)
      if 'forfeit' in hr.lower():
        w,l=(h,a) if hr.startswith('Won') else (a,h);games.append({'r':n,'div':d,'w':w,'l':l,'ff':True});continue
      if hs==as_: games.append({'r':n,'div':d,'w':h,'l':a,'ws':hs,'ls':as_,'draw':True});continue
      w,l,ws,ls=(h,a,hs,as_) if hs>as_ else (a,h,as_,hs)
      games.append({'r':n,'div':d,'w':w,'l':l,'ws':ws,'ls':ls})
  nextg=None
  if nxt:
    gl=[];byes=[]
    for r in byround[nxt]:
      d=parse(r['Grade'])[2]
      if r['Bye']: byes.append({'div':d,'team':clean(r['Bye'])});continue
      if r['Game Status']=='Final': continue
      gl.append({'date':dfmt(r['Game Date']) if r['Game Date'] else '','div':d,'h':clean(r['Home Team']),'a':clean(r['Away Team']),'time':tfmt(r['Time']),'t24':r['Time'] or '99:99','venue':r['Venue'],'court':r['Playing Surface'],'status':r['Game Status']})
    gl.sort(key=lambda g:(g['div'],g['t24'].zfill(5)))
    for g in gl: g.pop('t24')
    byes.sort(key=lambda b:b['div'])
    nextg={'r':nxt,'date':dates.get(nxt),'games':gl,'byes':byes}
  out['ages'][age]={'nights':dict(sorted(nights.items())),'dates':{str(k):v for k,v in dates.items() if k<=6},'played':played,'divisions':{d:sorted(set(v)) for d,v in sorted(divs.items())},'games':games,'next':nextg}
OVR=json.load(open(sys.argv[3])) if len(sys.argv)>3 else []
for o in OVR:
  nx=out['ages'].get(o['age'],{}).get('next')
  if not nx or nx['r']!=o['r']: continue
  for g in nx['games']:
    if g['div']==o['div'] and {g['h'],g['a']}==set(o['was']): g['h'],g['a']=o['now']; print('override',o)
missing=[a for a in AGES if a not in out['ages']]
if missing: raise SystemExit('Missing age groups: '+', '.join(missing))
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
for a,v in out['ages'].items(): print(a,v['nights'],'played',v['played'],'next',v['next']['r'] if v['next'] else None,{d:len(x) for d,x in v['divisions'].items()},len(v['games']))
print(out['asAt'])
