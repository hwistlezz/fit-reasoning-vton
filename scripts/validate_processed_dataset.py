#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from collections import Counter
def read(p):
    with open(p,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def exp(root,split,folder,pid):
    split='test' if split=='val' else split
    ext='.json' if folder=='quality' else ('_keypoints.json' if folder=='openpose-json' else ('.jpg' if folder in ['image','cloth','agnostic-v3.2'] else '.png'))
    return root/split/folder/(pid+ext if folder!='openpose-json' else pid+ext)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--pairs',required=True); ap.add_argument('--out-report',required=True); ap.add_argument('--out-failures',required=True); a=ap.parse_args()
    root=Path(a.root); pairs=read(a.pairs); req=['image','quality']; opt=['cloth','cloth-mask','image-parse','openpose-json','image-densepose','agnostic-v3.2','agnostic-mask']; fails=[]; cnt=Counter()
    for r in pairs:
        pid=r['pair_id']; split=r.get('split') or 'test'
        for folder in req+opt:
            if exp(root,split,folder,pid).exists(): cnt[folder]+=1
            elif folder in req: fails.append({'pair_id':pid,'split':split,'error_code':'MISSING_REQUIRED_ARTIFACT','artifact':folder})
    rep={'num_pairs':len(pairs),'artifact_counts':dict(cnt),'num_failures':len(fails)}; Path(a.out_report).parent.mkdir(parents=True,exist_ok=True); Path(a.out_report).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    with open(a.out_failures,'w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=['pair_id','split','error_code','artifact']); w.writeheader(); w.writerows(fails)
    print(json.dumps(rep,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
