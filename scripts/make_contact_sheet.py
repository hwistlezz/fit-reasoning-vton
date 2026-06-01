#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,math,random
from pathlib import Path
from PIL import Image,ImageDraw
def read(p):
    with open(p,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def fl(v):
    try: return float(v)
    except Exception: return 0.0
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--features',required=True); ap.add_argument('--processed-root',required=True); ap.add_argument('--output',required=True); ap.add_argument('--sample',type=int,default=100); ap.add_argument('--sort-by'); ap.add_argument('--shuffle',action='store_true'); a=ap.parse_args()
    rows=read(a.features)
    if a.sort_by and rows and a.sort_by in rows[0]: rows.sort(key=lambda r:fl(r.get(a.sort_by)),reverse=True)
    if a.shuffle: random.shuffle(rows)
    rows=rows[:a.sample]; tw,th,lh,cols=160,220,45,5; sheet=Image.new('RGB',(cols*tw,math.ceil(len(rows)/cols)*(th+lh)),'white'); d=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        x=(i%cols)*tw; y=(i//cols)*(th+lh); p=Path(r.get('image_path',''))
        if p.exists():
            try: im=Image.open(p).convert('RGB'); im.thumbnail((tw,th)); sheet.paste(im,(x+(tw-im.width)//2,y))
            except Exception: pass
        d.text((x+4,y+th+2),f"{r.get('pair_id','')}\n{r.get('fit_label','')}\nconf={r.get('confidence','')}",fill='black')
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); sheet.save(out,quality=90); print('[OK]',out)
if __name__=='__main__': main()
