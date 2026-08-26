from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import kendalltau
from sklearn.linear_model import LogisticRegression
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

HORIZON=730.5; SEEDS=[17,29,43,71,101]; FOLDS=5; EPS=1e-8

def logit(p):
 p=np.clip(np.asarray(p,float),EPS,1-EPS); return np.log(p/(1-p))
def sigmoid(x): return 1/(1+np.exp(-np.clip(np.asarray(x,float),-40,40)))
def targets_weights(duration,event,fit_duration,fit_event):
 duration=np.asarray(duration,float); event=np.asarray(event,int).astype(bool)
 censor=CensoringDistributionEstimator().fit(Surv.from_arrays(event=np.asarray(fit_event,int).astype(bool),time=np.asarray(fit_duration,float)))
 y=np.full(duration.shape,np.nan); w=np.zeros(duration.shape)
 case=(duration<=HORIZON)&event; control=duration>HORIZON; keep=case|control
 y[case]=1.; y[control]=0.; times=np.where(case,duration,HORIZON)
 if keep.any():
  g=censor.predict_proba(times[keep])
  if np.any(g<=0)|(~np.isfinite(g).all()): raise ValueError('invalid censoring survival')
  w[keep]=1/g
 return y,w

def fit_intercept(x,y,w):
 keep=w>0; x=x[keep]; y=y[keep]; w=w[keep]
 def obj(a):
  z=np.clip(a+x,-40,40); return float(np.sum(w*(np.logaddexp(0,z)-y*z)))
 return float(minimize_scalar(obj,bounds=(-20,20),method='bounded').x)
def fit_slope(x,y,w):
 keep=w>0
 if np.unique(y[keep]).size<2:return np.nan
 m=LogisticRegression(penalty=None,solver='lbfgs',max_iter=2000).fit(x[keep,None],y[keep].astype(int),sample_weight=w[keep])
 return float(m.coef_[0,0])
def evalm(y,w,raw,cand):
 keep=w>0; y=y[keep];w=w[keep];raw=raw[keep];cand=cand[keep]
 if len(y)==0:return {'ipcw_brier_raw':np.nan,'ipcw_brier_candidate':np.nan,'delta_ipcw_brier':np.nan,'citl_raw':np.nan,'citl_candidate':np.nan,'abs_citl_error_deterioration':np.nan,'slope_raw':np.nan,'slope_candidate':np.nan,'abs_slope_error_deterioration':np.nan,'n_evaluable':0,'events_evaluable':0}
 def b(p):return float(np.sum(w*(y-p)**2)/np.sum(w))
 xr=logit(raw);xc=logit(cand);cr=fit_intercept(xr,y,w);cc=fit_intercept(xc,y,w);sr=fit_slope(xr,y,w);sc=fit_slope(xc,y,w)
 return {'ipcw_brier_raw':b(raw),'ipcw_brier_candidate':b(cand),'delta_ipcw_brier':b(cand)-b(raw),'citl_raw':cr,'citl_candidate':cc,'abs_citl_error_deterioration':abs(cc)-abs(cr),'slope_raw':sr,'slope_candidate':sc,'abs_slope_error_deterioration':abs(sc-1)-abs(sr-1) if np.isfinite(sr) and np.isfinite(sc) else np.nan,'n_evaluable':int(len(y)),'events_evaluable':int(np.sum(y==1))}

def main():
 root=Path(__file__).resolve().parents[1]; pred=root/'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'; out=root/'research_studies/01_pattern_surv_hn/core_backbone/U5R2_V1R_anchor_preserving_bridge_exploration'
 data=pd.read_csv(pred,dtype={'acquisition_pattern':str,'usable_pattern':str}); specs=[{'candidate':f'anchor_blend_g{g:.2f}','gamma':g} for g in [0.,.10,.25,.50,.75,1.]]
 rows=[]; patterns=[]; pooled={s['candidate']:[] for s in specs}
 for seed in SEEDS:
  sd=data.loc[data.repetition_seed==seed]
  if len(sd)!=610:raise ValueError(seed)
  for fold in range(FOLDS):
   tr=sd.loc[sd.outer_fold!=fold].copy(); te=sd.loc[sd.outer_fold==fold].copy().reset_index(drop=True)
   _,tw=targets_weights(tr.duration_days,tr.event,tr.duration_days,~tr.event.astype(bool)); ty,ew=targets_weights(te.duration_days,te.event,tr.duration_days,~tr.event.astype(bool))
   raw=te.v1_risk_24m.to_numpy(float); v0=logit(te.v0_risk_24m.to_numpy(float)); v1=logit(raw)
   for s in specs:
    x=v0+s['gamma']*(v1-v0); p=sigmoid(x); m=evalm(ty,ew,raw,p); rows.append({**s,'seed':seed,'outer_fold':fold,**m}); pooled[s['candidate']].append((ty,ew,raw,p))
    for pat,idx in te.groupby('acquisition_pattern').groups.items():
     pos=np.asarray(list(idx),int); patterns.append({**s,'seed':seed,'outer_fold':fold,'pattern':str(pat),**evalm(ty[pos],ew[pos],raw[pos],p[pos])})
 fold=pd.DataFrame(rows); pat=pd.DataFrame(patterns); agg=[]
 for s in specs:
  y=np.concatenate([z[0] for z in pooled[s['candidate']]]);w=np.concatenate([z[1] for z in pooled[s['candidate']]]);r=np.concatenate([z[2] for z in pooled[s['candidate']]]);p=np.concatenate([z[3] for z in pooled[s['candidate']]])
  m=evalm(y,w,r,p); tau=kendalltau(r[w>0],p[w>0],nan_policy='omit').statistic
  # rank reversal count via discordant pairs on a deterministic sample/full evaluable set using rank order.
  rr=np.argsort(np.argsort(r[w>0]))!=np.argsort(np.argsort(p[w>0])); rank_changed=int(np.sum(rr))
  agg.append({**s,**m,'kendall_tau_raw_candidate':float(tau),'patients_with_changed_rank':rank_changed,'rank_change_fraction':float(rank_changed/len(rr))})
 agg=pd.DataFrame(agg); p_agg=[]
 for (cand,patn),g in pat.groupby(['candidate','pattern']):
  n=int(g.n_evaluable.sum());e=int(g.events_evaluable.sum())
  if n==0:continue
  br=float(np.average(g.ipcw_brier_raw.fillna(0),weights=g.n_evaluable));bc=float(np.average(g.ipcw_brier_candidate.fillna(0),weights=g.n_evaluable))
  p_agg.append({'candidate':cand,'pattern':patn,'n_evaluable':n,'events_evaluable':e,'delta_ipcw_brier':bc-br})
 p_agg=pd.DataFrame(p_agg); safety=[]
 for _,r in agg.iterrows():
  q=p_agg[(p_agg.candidate==r.candidate)&(p_agg.n_evaluable>=20)&(p_agg.events_evaluable>=5)]; worst=float(q.delta_ipcw_brier.max()) if len(q) else np.nan
  safety.append({'candidate':r.candidate,'gamma':r.gamma,'delta_ipcw_brier':r.delta_ipcw_brier,'worst_supported_pattern_regret':worst,'abs_citl_error_deterioration':r.abs_citl_error_deterioration,'abs_slope_error_deterioration':r.abs_slope_error_deterioration,'kendall_tau':r.kendall_tau_raw_candidate,'patients_with_changed_rank':r.patients_with_changed_rank,'passes_brier':bool(r.delta_ipcw_brier<=.005),'passes_pattern':bool(worst<=.020),'passes_citl_safety':bool(r.abs_citl_error_deterioration<=.10),'passes_slope_safety':bool(np.isfinite(r.abs_slope_error_deterioration) and r.abs_slope_error_deterioration<=.15)})
 safety=pd.DataFrame(safety); agg.to_csv(out/'anchor_bridge_aggregate_results.csv',index=False);fold.to_csv(out/'anchor_bridge_fold_results.csv',index=False);p_agg.to_csv(out/'anchor_bridge_pattern_aggregate_results.csv',index=False);safety.to_csv(out/'anchor_bridge_safety_audit.csv',index=False)
 result={'analysis':'U5R2 V1R anchor-preserving bridge development-only exploration','protocol':'frozen_anchor_bridge_exploration_protocol.yaml','candidate_count':len(specs),'safe_candidates':safety.loc[safety[['passes_brier','passes_pattern','passes_citl_safety','passes_slope_safety']].all(axis=1),'candidate'].tolist(),'aggregate':safety.to_dict(orient='records'),'patient_level_outputs':'not written'}
 (out/'anchor_bridge_exploration_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
