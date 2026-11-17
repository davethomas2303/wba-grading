"""Pull WBA fixtures and results from the PlayHQ public API and write them in the
same layout as PlayHQ's advanced fixture export (fx.csv), so s2gen.py is unchanged.

Environment: PLAYHQ_API_KEY, PLAYHQ_ORG_ID, optional PLAYHQ_TENANT, PLAYHQ_SEASON_ID.
Usage: python3 playhq_pull.py fx.csv
Public endpoints only; results appear once a game is finalised (PlayHQ support, Oct 2026).
"""
import csv,json,os,re,sys,time,urllib.request,urllib.error,urllib.parse,datetime
from zoneinfo import ZoneInfo
BASE='https://api.playhq.com'
KEY=os.environ['PLAYHQ_API_KEY'];ORG=os.environ['PLAYHQ_ORG_ID']
TENANT=os.environ.get('PLAYHQ_TENANT') or None
CALLS=0
def req(path,tenant=None):
  global CALLS;CALLS+=1
  r=urllib.request.Request(BASE+path,headers={'x-api-key':KEY,'x-phq-tenant':tenant or TENANT or '','Accept':'application/json'})
  for i in range(3):
    try:
      with urllib.request.urlopen(r,timeout=30) as f: return json.loads(f.read() or b'null')
    except urllib.error.HTTPError as e:
      if e.code in (429,502,503,504) and i<2: time.sleep(5*(i+1));continue
      raise SystemExit(f'PlayHQ {e.code} on {path}: {e.read()[:300]!r}')
def lst(path):
  out=[];cur=None
  for _ in range(50):
    p=req(path+(('&' if '?' in path else '?')+'cursor='+urllib.parse.quote(cur) if cur else ''))
    out+=(p or {}).get('data',[]);m=(p or {}).get('metadata') or {}
    cur=m.get('nextCursor') if m.get('hasMore') else None
    if not cur: break
  return out
def resolve_tenant():
  global TENANT
  if TENANT: return
  for c in ['basketball','bv','basketball-victoria']:
    try:
      urllib.request.urlopen(urllib.request.Request(f'{BASE}/v1/organisations/{ORG}/seasons',headers={'x-api-key':KEY,'x-phq-tenant':c,'Accept':'application/json'}),timeout=30)
      TENANT=c;print('tenant',c);return
    except urllib.error.HTTPError: pass
  raise SystemExit('No tenant value worked; set the PLAYHQ_TENANT secret.')
FINAL={'FINAL','COMPLETED','COMPLETE','FINALISED','FINALIZED','FORFEIT','FORFEITED'}
COLS=["Game Date","Grade","Grade Type","Round","Game Status","Venue","Playing Surface","Time","Home Team","Home Team Score","Home Team Result","Home Team Players In Lineup","Home Team Player Points","Away Team","Away Team Score","Away Team Result","Away Team Players In Lineup","Away Team Player Points","Bye","Host Organisation","Competition","Competition Type","Season","Game Alias","Game Code","Game ID","Result Source","Result Timestamp (last updated)","Last Updated At","Last Updated By","Last Updated By Organisation"]
def result(c,game_ff):
  o=str(c.get('outcome') or '').upper()
  ff=game_ff or 'FORFEIT' in o
  if 'WIN' in o or o=='WON': return 'Won by forfeit' if ff else 'Won'
  if 'LOS' in o: return 'Lost by forfeit' if ff else 'Lost'
  if 'DRAW' in o: return 'Drew'
  return ''
def main(out):
  resolve_tenant()
  seasons=[s for s in lst(f'/v1/organisations/{ORG}/seasons') if (os.environ.get('PLAYHQ_SEASON_ID') and s['id']==os.environ['PLAYHQ_SEASON_ID']) or (not os.environ.get('PLAYHQ_SEASON_ID') and str(s.get('status','')).upper()=='ACTIVE')]
  if not seasons: raise SystemExit('No active season found; set PLAYHQ_SEASON_ID.')
  now=datetime.datetime.now(ZoneInfo('Australia/Melbourne')).strftime('%d/%m/%Y %H:%M')
  rows=[];statuses=set();outcomes=set()
  for s in seasons:
    print('season',s.get('name'),'|',(s.get('competition') or {}).get('name'))
    for g in lst(f"/v1/seasons/{s['id']}/grades"):
      gname=g.get('name','')
      if not re.match(r'\w+day U\d+(?:/\d+)? (?:Boys|Girls)',gname): continue
      for x in lst(f"/v1/grades/{g['id']}/games"):
        st=str(x.get('status') or '').upper();statuses.add(st)
        comps=x.get('competitors') or []
        for c in comps: outcomes.add(str(c.get('outcome')))
        sc=x.get('schedule') or {};d=sc.get('date') or ''
        r=dict.fromkeys(COLS,'')
        r.update({'Game Date':datetime.date.fromisoformat(d).strftime('%d/%m/%Y') if d else '','Grade':gname,'Round':(x.get('round') or {}).get('name',''),
          'Venue':(x.get('venue') or {}).get('name',''),'Playing Surface':(x.get('venue') or {}).get('surfaceName',''),'Time':(sc.get('time') or '')[:5],
          'Season':s.get('name',''),'Game ID':x.get('id',''),'Last Updated At':now,'Result Source':'PlayHQ API'})
        real=[c for c in comps if not c.get('isBye') and c.get('name')]
        if x.get('isBye') or len(real)==1:
          r['Bye']=real[0]['name'] if real else '';rows.append(r);continue
        if len(real)<2: continue
        h=next((c for c in real if c.get('isHomeTeam')),real[0]);a=real[1] if h is real[0] else real[0]
        ff='FORFEIT' in st
        r.update({'Home Team':h['name'],'Away Team':a['name']})
        if st in FINAL:
          r['Game Status']='Final'
          for k,c in (('Home',h),('Away',a)):
            r[f'{k} Team Score']='' if c.get('scoreTotal') is None else str(c['scoreTotal']);r[f'{k} Team Result']=result(c,ff)
          if not r['Home Team Result'] and r['Home Team Score'] and r['Away Team Score']:
            hs,as_=int(r['Home Team Score']),int(r['Away Team Score'])
            r['Home Team Result'],r['Away Team Result']=('Drew','Drew') if hs==as_ else (('Won','Lost') if hs>as_ else ('Lost','Won'))
        else: r['Game Status']=st.title() or 'Upcoming'
        rows.append(r)
  junior=[r for r in rows if r['Game Status']=='Final']
  if len(rows)<100 or len(junior)<50: raise SystemExit(f'Only {len(rows)} rows ({len(junior)} final) came back; not overwriting. Check grade names and season.')
  with open(out,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,COLS,quoting=csv.QUOTE_ALL);w.writeheader();w.writerows(rows)
  print(len(rows),'rows;',CALLS,'API calls; statuses',sorted(statuses),'outcomes',sorted(outcomes))
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else 'fx.csv')
