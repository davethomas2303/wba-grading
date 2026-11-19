"""Aggregate the Warriors CRP squad / domestic team match file into counts only (no names).
Usage: python3 repgen.py warriors_matches.csv rep.json   (keep the source CSV out of this public repo)"""
import csv,json,re,sys,collections
src=open('gen.py').read().split('\n');exec('\n'.join(src[2:19]))
SQ_RANK={'1':1,'2':2,'Black':2,'3':3,'Red':3,'White':4}
def squad_short(s):
  m=re.match(r'(U\d+ (?:Boys|Girls))(?: (.+))?$',s.strip()); return m.group(1),(m.group(2) or 'Squad')
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig')))
out={'source':'Warriors Country Representative Program 2026/27 squads matched to PlayHQ domestic teams','squads':{},'teams':[],'unmatched':collections.Counter(),'noteam':collections.Counter()}
teams=collections.defaultdict(lambda:collections.Counter())
meta={}
for r in rows:
  sage,sname=squad_short(r['Warriors squad'])
  out['squads'].setdefault(r['Warriors squad'],{'age':sage,'name':sname,'rank':SQ_RANK.get(sname,1),'players':0})
  out['squads'][r['Warriors squad']]['players']+=1
  if r['Match status']=='Unmatched': out['unmatched'][r['Warriors squad']]+=1;continue
  if not r['Domestic team']: out['noteam'][r['Warriors squad']]+=1;continue
  g=r['Domestic grade'];m=re.match(r'\w+day (U\d+(?:/\d+)? (?:Boys|Girls))(?: (D\d))?',g)
  age,div=m.group(1),(m.group(2) or 'D1')
  name=clean(r['Domestic team'])
  k=(age,name);teams[k][r['Warriors squad']]+=1;meta[k]={'age':age,'team':name,'club':club(name),'div':div}
for k,c in teams.items(): out['teams'].append({**meta[k],'squads':dict(c),'n':sum(c.values())})
out['teams'].sort(key=lambda x:(x['age'],x['div'],-x['n'],x['team']))
out['unmatched']=dict(out['unmatched']);out['noteam']=dict(out['noteam'])
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
print(len(rows),'players;',sum(t['n'] for t in out['teams']),'in domestic teams;',sum(out['unmatched'].values()),'unmatched;',sum(out['noteam'].values()),'no team')
