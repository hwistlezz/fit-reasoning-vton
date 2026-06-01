#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm
COCO={'nose':0,'neck':1,'right_shoulder':2,'right_elbow':3,'right_wrist':4,'left_shoulder':5,'left_elbow':6,'left_wrist':7,'right_hip':8,'right_knee':9,'right_ankle':10,'left_hip':11,'left_knee':12,'left_ankle':13}
UPPER={5,6,7}
def read_csv(p):
    with open(p,newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def dist(a,b): return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)
def kps(p):
    if not p.exists(): return {}
    try: obj=json.load(open(p,encoding='utf-8'))
    except Exception: return {}
    people=obj.get('people') if isinstance(obj,dict) else None
    if isinstance(people,list) and people:
        arr=people[0].get('pose_keypoints_2d',[]); out={}
        for name,idx in COCO.items():
            j=idx*3
            if j+2<len(arr): out[name]=(float(arr[j]),float(arr[j+1]),float(arr[j+2]))
        return out
    return {}
def xy(d,name):
    v=d.get(name)
    if not v or v[2]<0.05 or v[0]<=0 or v[1]<=0: return None
    return (v[0],v[1])
def parse_mask(p):
    if not p.exists(): return None
    arr=np.array(Image.open(p)); return arr[:,:,0] if arr.ndim==3 else arr
def width(mask,y,band=8):
    h,w=mask.shape; sub=mask[max(0,y-band):min(h,y+band+1)]; xs=np.where(sub>0)[1]
    return float(xs.max()-xs.min()+1) if len(xs) else None
def label(f):
    if f['confidence']<60: return 'unknown_low_confidence'
    sr,tr,gl=f.get('shoulder_ratio'),f.get('torso_width_ratio'),f.get('garment_length_ratio')
    if sr and tr and gl and sr>1.18 and tr>1.22 and gl>1.12: return 'oversized'
    if (sr and sr>1.10) or (tr and tr>1.15): return 'slightly_oversized'
    if sr and tr and 0.95<=sr<=1.06 and 0.95<=tr<=1.08: return 'fitted_or_slim_direction'
    return 'regular'
def ann(key,lab,text,x,y,w,h,val): return {'key':key,'label':lab,'text':text,'x':round(x/max(1,w)*100,2),'y':round(y/max(1,h)*100,2),'value':None if val is None else round(float(val),4)}
def one(pair,root,save_json,save_ann):
    pid=pair['pair_id']; split='test' if pair.get('split')=='val' else (pair.get('split') or 'test')
    img=root/split/'image'/f'{pid}.jpg'; kp=root/split/'openpose-json'/f'{pid}_keypoints.json'; pm=root/split/'image-parse'/f'{pid}.png'
    w=h=0
    if img.exists():
        with Image.open(img) as im: w,h=im.size
    d=kps(kp); arr=parse_mask(pm)
    ls,rs,lh,rh,lw,rw=[xy(d,n) for n in ['left_shoulder','right_shoulder','left_hip','right_hip','left_wrist','right_wrist']]
    f={'pair_id':pid,'image_path':str(img),'cloth_path':str(root/split/'cloth'/f'{pid}.jpg'),'cloth_id':pair.get('cloth_id',''),'model_id':pair.get('model_id',''),'pose':pair.get('pose','unknown'),'angle':pair.get('angle','unknown'),'cloth_type':pair.get('category','unknown'),'shoulder_ratio':None,'torso_width_ratio':None,'sleeve_length_ratio':None,'garment_length_ratio':None,'silhouette_score':None,'pose_quality':min(1.0,sum(1 for v in d.values() if v[2]>0.05)/14.0),'parsing_quality':0.0,'body_visibility':0.0,'quality_score':0.0,'confidence':0.0,'fit_label':'unknown_low_confidence'}
    anns=[]
    if arr is not None:
        upper=np.isin(arr,list(UPPER)).astype(np.uint8); body=(arr>0).astype(np.uint8); f['parsing_quality']=min(1.0,float(upper.sum())/max(1,arr.size*0.08)); f['body_visibility']=min(1.0,float(body.sum())/max(1,arr.size*0.20))
        if ls and rs:
            sy=int((ls[1]+rs[1])/2); bw=dist(ls,rs); gw=width(upper,sy)
            if bw>1 and gw: f['shoulder_ratio']=gw/bw
        if ls and rs and lh and rh:
            sy=int((ls[1]+rs[1])/2); hy=int((lh[1]+rh[1])/2); cy=int(sy*.65+hy*.35); bw=width(body,cy); gw=width(upper,cy)
            if bw and gw: f['torso_width_ratio']=gw/bw
            ys=np.where(upper>0)[0]
            if len(ys) and hy>sy: f['garment_length_ratio']=(int(ys.max())-sy)/max(1,hy-sy)
    if ls and lw: f['sleeve_length_ratio']=1.0
    elif rs and rw: f['sleeve_length_ratio']=1.0
    conf=.30*f['pose_quality']+.25*f['parsing_quality']+.20*f['body_visibility']+.15*.5+.10*.5; f['quality_score']=round(conf,4); f['confidence']=round(conf*100,2); f['fit_label']=label(f)
    if save_ann and w and h:
        if ls and rs: anns.append(ann('shoulder','어깨','어깨선과 신체 어깨 위치를 비교합니다.',(ls[0]+rs[0])/2,(ls[1]+rs[1])/2,w,h,f['shoulder_ratio']))
        if ls and rs and lh and rh: anns.append(ann('torso','몸통','몸통 폭과 의류 여유분을 비교합니다.',(ls[0]+rs[0]+lh[0]+rh[0])/4,(ls[1]+rs[1]+lh[1]+rh[1])/4,w,h,f['torso_width_ratio'])); anns.append(ann('length','기장','상의 기장이 골반 기준으로 어느 정도 내려오는지 봅니다.',(lh[0]+rh[0])/2,(lh[1]+rh[1])/2,w,h,f['garment_length_ratio']))
        wrist=lw or rw
        if wrist: anns.append(ann('sleeve','소매','소매 끝 위치와 손목 위치를 비교합니다.',wrist[0],wrist[1],w,h,f['sleeve_length_ratio']))
    if save_json:
        fd=root/split/'fit'; fd.mkdir(parents=True,exist_ok=True); (fd/f'{pid}.json').write_text(json.dumps({'pair_id':pid,'fit_label':f['fit_label'],'confidence':f['confidence'],'features':{k:f[k] for k in ['shoulder_ratio','torso_width_ratio','sleeve_length_ratio','garment_length_ratio','pose_quality','parsing_quality','body_visibility','quality_score']},'annotations':anns},ensure_ascii=False,indent=2),encoding='utf-8')
    return f
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--pairs',required=True); ap.add_argument('--output',required=True); ap.add_argument('--save-fit-json',action='store_true'); ap.add_argument('--save-annotations',action='store_true'); ap.add_argument('--limit',type=int); ap.add_argument('--save-failures',action='store_true'); ap.add_argument('--resume',action='store_true'); a=ap.parse_args()
    pairs=read_csv(a.pairs); pairs=pairs[:a.limit] if a.limit else pairs; rows=[one(p,Path(a.input),a.save_fit_json,a.save_annotations) for p in tqdm(pairs,desc='fit')]
    fields=['pair_id','image_path','cloth_path','cloth_id','model_id','pose','angle','cloth_type','shoulder_ratio','torso_width_ratio','sleeve_length_ratio','garment_length_ratio','silhouette_score','pose_quality','parsing_quality','body_visibility','quality_score','confidence','fit_label']
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print('[OK]',out)
if __name__=='__main__': main()
