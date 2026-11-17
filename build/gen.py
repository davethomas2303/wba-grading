import csv,collections,re,json,sys
rows=list(csv.DictReader(open('csvin/fx.csv',encoding='utf-8-sig')))
AGES=["U19 Boys","U16/19 Girls","U16 Boys","U14 Boys","U14 Girls","U12 Boys","U12 Girls","U10 Boys"]
def clean(n):
  n=re.sub(r'\s+',' ',n).strip()
  one=bool(re.search(r'\bU\d+\.1 ',n))
  n=re.sub(r'\bU\d+(?:\.\d)?(?:/\d+)? (?:Boys|Girls)\b','',n)
  n=' '.join(x.title() if x.isupper() and len(x)>2 else x for x in n.split())+(' 1' if one else '')
  n=re.sub(r'\bGladiator\b','Gladiators',n)
  w=n.split(); out=[]
  for x in w:
    if not out or out[-1]!=x: out.append(x)
  n=' '.join(out)
  m=re.match(r'Gladiators (.*)',n)
  return n
def club(n):
  for c,k in [('Bunyip','Bunyip'),('Chalkies','Chalkies'),('Devils','Devils'),('Neerim Wolves','Neerim Wolves'),('Rebels','Rebels'),('Warranor','Warranor'),('Yarragon','Yarragon'),('Gladiators','Gladiators')]:
    if n.startswith(c): return k
  raise SystemExit('club? '+n)
def parse(g):
  m=re.match(r'\w+day (U\d+(?:/\d+)? (?:Boys|Girls))(?: (D\d))?$',g)
  return (m.group(1),m.group(2) or 'D1') if m else (None,None)
out={}
for age in AGES:
  rs=[x for x in rows if x['Round'] in ('Round 1','Round 2','Round 3') and parse(x['Grade'])[0]==age]
  teams={}
  for x in rs:
    d=parse(x['Grade'])[1]
    for k in ('Home Team','Away Team','Bye'):
      if x[k]:
        n=clean(x[k]); assert teams.get(n,d)==d,('dup',age,n,teams.get(n),d); teams[n]=d
  real=[x for x in rs if x['Home Team'] and x['Away Team']]
  played=0
  for r in (1,2,3):
    g=[x for x in real if x['Round']==f'Round {r}']
    if g and sum(x['Game Status']=='Final' for x in g)>=0.75*len(g): played=r
    else: break
  games=[]
  for x in real:
    r=int(x['Round'].split()[-1])
    if r>played: continue
    d=parse(x['Grade'])[1];h,a=clean(x['Home Team']),clean(x['Away Team']);hr=x['Home Team Result']
    if x['Game Status']!='Final':
      games.append(dict(r=r,div=d,w=h,l=a,pending=True)); print('  pending',age,r,d,h,'v',a,x['Game Status']); continue
    hs,as_=int(float(x['Home Team Score'] or 0)),int(float(x['Away Team Score'] or 0))
    if hr=='Drew': games.append(dict(r=r,div=d,w=h,l=a,ws=hs,ls=as_,draw=True))
    elif 'forfeit' in hr: games.append(dict(r=r,div=d,w=h if hr.startswith('Won') else a,l=a if hr.startswith('Won') else h,ff=True))
    elif hr.startswith('Won'): games.append(dict(r=r,div=d,w=h,l=a,ws=hs,ls=as_))
    elif hr.startswith('Lost'): games.append(dict(r=r,div=d,w=a,l=h,ws=as_,ls=hs))
    else: raise SystemExit('result? '+repr(hr))
  out[age]=dict(teams=[dict(name=n,club=club(n),stage1=d) for n,d in sorted(teams.items(),key=lambda z:(z[1],z[0]))],games=sorted(games,key=lambda g:(g['r'],g['div'])),played=played)
  print(age,len(teams),'teams',len(games),'games','rounds',played, collections.Counter(d for d in teams.values()))
json.dump(out,open('gen_out.json','w'),indent=1)
