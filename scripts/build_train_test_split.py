#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,random
from pathlib import Path
def read(p):
    with open(p,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',required=True); ap.add_argument('--features'); ap.add_argument('--output-root',required=True); ap.add_argument('--train-ratio',type=float,default=.8); ap.add_argument('--val-ratio',type=float,default=.1); ap.add_argument('--test-ratio',type=float,default=.1); ap.add_argument('--seed',type=int,default=42); a=ap.parse_args()
    rows=read(a.pairs); random.Random(a.seed).shuffle(rows); n=len(rows); nt=int(n*a.train_ratio); nv=int(n*a.val_ratio); splits={'train':rows[:nt],'val':rows[nt:nt+nv],'test':rows[nt+nv:]}; out=Path(a.output_root); out.mkdir(parents=True,exist_ok=True)
    allrows=[]
    for name,rs in splits.items():
        with (out/f'{name}_pairs.txt').open('w',encoding='utf-8') as f:
            for r in rs: f.write(f"{r['pair_id']}.jpg {r['pair_id']}.jpg\n"); r['split']=name; allrows+=rs
    fields=sorted(set().union(*(r.keys() for r in allrows))) if allrows else []
    with (out/'metadata.csv').open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(allrows)
    print({k:len(v) for k,v in splits.items()})
if __name__=='__main__': main()
