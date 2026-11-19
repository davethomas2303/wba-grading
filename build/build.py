"""Inject the data files into template.html and write the site to ../index.html."""
import json,os
H=os.path.dirname(os.path.abspath(__file__));j=lambda f:json.load(open(os.path.join(H,f)))
t=open(os.path.join(H,'template.html')).read()
t=t.replace('__LOGOS__',json.dumps(j('club_logos.json'))).replace('__WBALOGO__',json.dumps(open(os.path.join(H,'logo.txt')).read()))
t=t.replace('__STAGE2__',json.dumps(j('s2.json'),ensure_ascii=False)).replace('__W26__',json.dumps(j('w26_bench.json'))).replace('__REP__',json.dumps(j('rep.json'),ensure_ascii=False))
open(os.path.join(H,'..','index.html'),'w').write(t);print('index.html written')
