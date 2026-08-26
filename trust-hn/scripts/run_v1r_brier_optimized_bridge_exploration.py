from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from sklearn.linear_model import LogisticRegression
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv
from scipy.stats import kendalltau
H=730.5;SEEDS=[17,29,43,71,101];FOLDS=5;EPS=1e-8

def logit(p):p=np.clip(np.asarray(p,float),EPS,1-EPS);return np.log(p/(1-p))
def sigmoid(x):return 1/(1+np.exp(-np.clip(np.asarray(x,float),-40,40)))
def tw(d,e,fd,fe):
 d=np.asarray(d,float);e=np.asarray(e,int).astype(bool);c=CensoringDistributionEstimator().fit(Surv.from_arrays(event=np.asarray(fe,int).astype(bool),time=np.asarray(fd,float)));y=np.full(d.shape,np.nan);w=np.zeros(d.shape);case=(d<=H)&e;control=d>H;keep=case|control;y[case]=1;y[control]=0;t=np.where(case,d,H)
 if keep.any():
  g=c.predict_proba(t[keep]);
  if np.any(g<=0) or not np.isfinite(g).all():raise ValueError('bad censoring')
  w[keep]=1/g
 return y,w
def fit_brier(x,y,w):
 keep=w>0;x=x[keep];y=y[keep];w=w[keep]
 def obj(z):
  a,b=z;p=sigmoid(a+b*x);return float(np.sum(w*(y-p)**2)/np.sum(w))
 res=minimize(obj,[0.,1.],method='L-BFGS-B',bounds=[(-10,10),(.75,1.25)],options={'maxiter':1000,'ftol':1e-14})
 if not res.success:raise RuntimeError(res.message)
 return float(res.x[0]),float(res.x[1])
def fit_citl(x,y,w):
 keep=w>0;x=x[keep];y=y[keep];w=w[keep]
 def obj(a):
  z=np.clip(a+x,-40,40);return float(np.sum(w*(np.logaddexp(0,z)-y*z)))
 return float(minimize_scalar(obj,bounds=(-20,20),method='bounded').x)
def fit_slope(x,y,w):
 keep=w>0
 if np.unique(y[keep]).size<2:return np.nan
 m=LogisticRegression(penalty=None,solver='lbfgs',max_iter=2000).fit(x[keep,None],y[keep].astype(int),sample_weight=w[keep]);return float(m.coef_[0,0])
def ev(y,w,raw,cand):
 keep=w>0;y=y[keep];w=w[keep];raw=raw[keep];cand=cand[keep]
 if len(y)==0:return {'ipcw_brier_raw':np.nan,'ipcw_brier_candidate':np.nan,'delta_ipcw_brier':np.nan,'citl_raw':np.nan,'citl_candidate':np.nan,'abs_citl_error_deterioration':np.nan,'slope_raw':np.nan,'slope_candidate':np.nan,'abs_slope_error_deterioration':np.nan,'n_evaluable':0,'events_evaluable':0}
 def b(p):return float(np.sum(w*(y-p)**2)/np.sum(w))
 xr=logit(raw);xc=logit(cand);cr=fit_citl(xr,y,w);cc=fit_citl(xc,y,w);sr=fit_slope(xr,y,w);sc=fit_slope(xc,y,w)
 return {'ipcw_brier_raw':b(raw),'ipcw_brier_candidate':b(cand),'delta_ipcw_brier':b(cand)-b(raw),'citl_raw':cr,'citl_candidate':cc,'abs_citl_error_deterioration':abs(cc)-abs(cr),'slope_raw':sr,'slope_candidate':sc,'abs_slope_error_deterioration':abs(sc-1)-abs(sr-1) if np.isfinite(sr) and np.isfinite(sc) else np.nan,'n_evaluable':int(len(y)),'events_evaluable':int(np.sum(y==1))}
def main():
 root=Path(__file__).resolve().parents[1];pred=root/'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv';out=root/'research_studies/01_pattern_surv_hn/core_backbone/U5R3_V1R_brier_optimized_bridge_exploration';data=pd.read_csv(pred,dtype={'acquisition_pattern':str,'usable_pattern':str});specs=[{'candidate':f'brier_full_shrinkage_g{g:.2f}','gamma':g} for g in [.10,.25,.50,.75,1.]];rows=[];pars=[];pats=[];pool={s['candidate']:[] for s in specs}
 for seed in SEEDS:
  sd=data[data.repetition_seed==seed]
  for fold in range(FOLDS):
   tr=sd[sd.outer_fold!=fold];te=sd[sd.outer_fold==fold].copy().reset_index(drop=True);_,twgt=tw(tr.duration_days,tr.event,tr.duration_days,~tr.event.astype(bool));ty,ew=tw(te.duration_days,te.event,tr.duration_days,~tr.event.astype(bool));xtr=logit(tr.v1_risk_24m.to_numpy(float));a,b=fit_brier(xtr,ty*0+0 if False else np.where(twgt>0,0,0),twgt) if False else fit_brier(xtr, np.where(np.asarray(twgt)>0, np.nan_to_num(np.where((np.asarray(tr.duration_days)<=H)&tr.event,1,np.where(np.asarray(tr.duration_days)>H,0,np.nan)),nan=0),0), twgt)
   # Recompute training targets explicitly for fit.
   ytr,wtr=tw(tr.duration_days,tr.event,tr.duration_days,~tr.event.astype(bool));a,b=fit_brier(xtr,ytr,wtr);pars.append({'seed':seed,'outer_fold':fold,'alpha_brier':a,'beta_brier':b});raw=te.v1_risk_24m.to_numpy(float);x=logit(raw)
   for s in specs:
    xc=x+s['gamma']*(a+b*x-x);p=sigmoid(xc);m=ev(ty,ew,raw,p);rows.append({**s,'seed':seed,'outer_fold':fold,'alpha_brier':a,'beta_brier':b,'beta_effective':1+s['gamma']*(b-1),**m});pool[s['candidate']].append((ty,ew,raw,p))
    for pat,idx in te.groupby('acquisition_pattern').groups.items():
     pos=np.asarray(list(idx),int);pats.append({**s,'seed':seed,'outer_fold':fold,'pattern':str(pat),**ev(ty[pos],ew[pos],raw[pos],p[pos])})
 fold=pd.DataFrame(rows);pat=pd.DataFrame(pats);agg=[]
 for s in specs:
  y=np.concatenate([z[0] for z in pool[s['candidate']]]);w=np.concatenate([z[1] for z in pool[s['candidate']]]);r=np.concatenate([z[2] for z in pool[s['candidate']]]);p=np.concatenate([z[3] for z in pool[s['candidate']]]);m=ev(y,w,r,p);tau=kendalltau(r[w>0],p[w>0]).statistic;agg.append({**s,**m,'kendall_tau':float(tau)})
 agg=pd.DataFrame(agg);pa=[]
 for (c,pt),g in pat.groupby(['candidate','pattern']):
  n=int(g.n_evaluable.sum());e=int(g.events_evaluable.sum())
  if n==0:continue
  br=float(np.average(g.ipcw_brier_raw.fillna(0),weights=g.n_evaluable));bc=float(np.average(g.ipcw_brier_candidate.fillna(0),weights=g.n_evaluable));pa.append({'candidate':c,'pattern':pt,'n_evaluable':n,'events_evaluable':e,'delta_ipcw_brier':bc-br})
 pa=pd.DataFrame(pa);audit=[]
 for _,r in agg.iterrows():
  q=pa[(pa.candidate==r.candidate)&(pa.n_evaluable>=20)&(pa.events_evaluable>=5)];worst=float(q.delta_ipcw_brier.max()) if len(q) else np.nan;audit.append({'candidate':r.candidate,'delta_ipcw_brier':r.delta_ipcw_brier,'worst_supported_pattern_regret':worst,'abs_citl_error_deterioration':r.abs_citl_error_deterioration,'abs_slope_error_deterioration':r.abs_slope_error_deterioration,'kendall_tau':r.kendall_tau,'passes_all':bool(r.delta_ipcw_brier<=.005 and worst<=.02 and r.abs_citl_error_deterioration<=.1 and r.abs_slope_error_deterioration<=.15)})
 audit=pd.DataFrame(audit);agg.to_csv(out/'brier_optimized_aggregate_results.csv',index=False);fold.to_csv(out/'brier_optimized_fold_results.csv',index=False);pa.to_csv(out/'brier_optimized_pattern_aggregate_results.csv',index=False);pd.DataFrame(pars).to_csv(out/'brier_optimized_parameters.csv',index=False);audit.to_csv(out/'brier_optimized_safety_audit.csv',index=False);res={'analysis':'U5R3 V1R Brier-optimized monotone bridge exploration','protocol':'frozen_brier_optimized_bridge_protocol.yaml','aggregate':audit.to_dict(orient='records'),'patient_level_outputs':'not written'};(out/'brier_optimized_exploration_summary.json').write_text(json.dumps(res,indent=2),encoding='utf-8');print(json.dumps(res,indent=2))
if __name__=='__main__':main()
