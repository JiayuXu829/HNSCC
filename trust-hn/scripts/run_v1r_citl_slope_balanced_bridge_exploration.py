from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sksurv.nonparametric import CensoringDistributionEstimator
from sksurv.util import Surv

HORIZON = 730.5
SEEDS = [17, 29, 43, 71, 101]
FOLDS = 5
EPS = 1e-8
EXPECTED_PER_SEED = 610
BETAS = [0.90, 0.925, 0.95, 0.975]
MODES = ['brier', 'mix_25', 'mix_50', 'mix_75', 'logloss']


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    return np.log(p / (1.0 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(np.asarray(x, dtype=float), -40.0, 40.0)))


def targets_weights(duration, event, fit_duration, fit_event):
    duration = np.asarray(duration, float); event = np.asarray(event, int).astype(bool)
    fit_duration = np.asarray(fit_duration, float); fit_event = np.asarray(fit_event, int).astype(bool)
    censor = CensoringDistributionEstimator().fit(Surv.from_arrays(event=fit_event, time=fit_duration))
    target = np.full(duration.shape, np.nan); weight = np.zeros(duration.shape)
    case = (duration <= HORIZON) & event; control = duration > HORIZON; included = case | control
    target[case] = 1.0; target[control] = 0.0
    times = np.where(case, duration, HORIZON)
    if included.any():
        g = censor.predict_proba(times[included])
        if np.any(g <= 0) or not np.isfinite(g).all(): raise ValueError('invalid censoring survival')
        weight[included] = 1.0 / g
    return target, weight


def fit_alpha(x, y, w, beta, mode):
    keep = w > 0; x = np.asarray(x[keep], float); y = np.asarray(y[keep], float); w = np.asarray(w[keep], float)
    def objective(alpha, kind):
        z = np.clip(alpha + beta*x, -40, 40); p = sigmoid(z)
        if kind == 'brier': return float(np.sum(w*(y-p)**2)/np.sum(w))
        return float(np.sum(w*(np.logaddexp(0,z)-y*z))/np.sum(w))
    if mode == 'brier':
        kind, mix = 'brier', None
    elif mode == 'logloss':
        kind, mix = 'logloss', None
    else:
        kind, mix = 'mix', {'mix_25':0.25,'mix_50':0.50,'mix_75':0.75}[mode]
    def obj(alpha):
        if kind != 'mix': return objective(alpha, kind)
        return (1-mix)*objective(alpha, 'brier') + mix*objective(alpha, 'logloss')
    result = minimize_scalar(obj, bounds=(-20,20), method='bounded', options={'xatol':1e-13, 'maxiter':2000})
    if not result.success: raise RuntimeError(str(result.message))
    return float(result.x), float(result.fun)


def fit_citl(x, y, w):
    keep=w>0; x=np.asarray(x[keep],float); y=np.asarray(y[keep],float); w=np.asarray(w[keep],float); lo,hi=-20.,20.
    for _ in range(120):
        mid=(lo+hi)/2; score=np.sum(w*(y-sigmoid(mid+x)))
        if score>0: lo=mid
        else: hi=mid
    return (lo+hi)/2


def fit_slope(x, y, w):
    from scipy.optimize import minimize
    keep=w>0; x=np.asarray(x[keep],float); y=np.asarray(y[keep],float); w=np.asarray(w[keep],float)
    if len(x)==0 or np.unique(y).size<2: return np.nan
    def obj(params):
        z=np.clip(params[0]+params[1]*x,-40,40)
        return float(np.sum(w*(np.logaddexp(0,z)-y*z)))
    r=minimize(obj,[0.,1.],method='L-BFGS-B',bounds=[(-20,20),(-20,20)],options={'ftol':1e-15,'gtol':1e-10,'maxiter':2000})
    return float(r.x[1]) if r.success else np.nan


def metrics(target, weight, raw, candidate):
    keep=np.asarray(weight)>0; target=np.asarray(target)[keep]; weight=np.asarray(weight,float)[keep]; raw=np.asarray(raw,float)[keep]; candidate=np.asarray(candidate,float)[keep]
    if len(target)==0 or np.sum(weight)<=0:
        return {'ipcw_brier_raw':np.nan,'ipcw_brier_candidate':np.nan,'delta_ipcw_brier':np.nan,'citl_raw':np.nan,'citl_candidate':np.nan,'abs_citl_error_deterioration':np.nan,'calibration_slope_raw':np.nan,'calibration_slope_candidate':np.nan,'abs_slope_error_deterioration':np.nan,'n_evaluable':0,'events_evaluable':0}
    br=np.sum(weight*(target-raw)**2)/np.sum(weight); bc=np.sum(weight*(target-candidate)**2)/np.sum(weight)
    xr,xc=logit(raw),logit(candidate); cr,cc=fit_citl(xr,target,weight),fit_citl(xc,target,weight); sr,sc=fit_slope(xr,target,weight),fit_slope(xc,target,weight)
    return {'ipcw_brier_raw':float(br),'ipcw_brier_candidate':float(bc),'delta_ipcw_brier':float(bc-br),'citl_raw':float(cr),'citl_candidate':float(cc),'abs_citl_error_deterioration':float(abs(cc)-abs(cr)),'calibration_slope_raw':float(sr),'calibration_slope_candidate':float(sc),'abs_slope_error_deterioration':float(abs(sc-1)-abs(sr-1)) if np.isfinite(sr) and np.isfinite(sc) else np.nan,'n_evaluable':int(len(target)),'events_evaluable':int(np.sum(target==1))}


def main():
    root=Path(__file__).resolve().parents[1]; pred=root/'results/predictions/pattern_surv_hn/U2_V1R/v1_repeated_nested_oof_predictions.csv'; out=root/'research_studies/01_pattern_surv_hn/core_backbone/U5R6_V1R_citl_slope_balanced_bridge_exploration'; out.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(pred,dtype={'acquisition_pattern':str,'usable_pattern':str}); required={'repetition_seed','outer_fold','duration_days','event','acquisition_pattern','v1_risk_24m'}; missing=required-set(data.columns)
    if missing: raise ValueError(sorted(missing))
    candidates=[{'candidate':f'beta_{b:.3f}_{m}','beta':b,'mode':m} for b in BETAS for m in MODES]
    pooled={c['candidate']:[] for c in candidates}; folds=[]; patterns=[]; params=[]
    for seed in SEEDS:
        sd=data.loc[data.repetition_seed==seed].copy()
        if len(sd)!=EXPECTED_PER_SEED: raise ValueError(f'{seed}: {len(sd)}')
        for fold in range(FOLDS):
            tr=sd.loc[sd.outer_fold!=fold].copy().reset_index(drop=True); te=sd.loc[sd.outer_fold==fold].copy().reset_index(drop=True)
            ty,tw=targets_weights(tr.duration_days,tr.event,tr.duration_days,~tr.event.astype(bool)); vy,vw=targets_weights(te.duration_days,te.event,tr.duration_days,~tr.event.astype(bool)); xt,xv=logit(tr.v1_risk_24m.to_numpy(float)),logit(te.v1_risk_24m.to_numpy(float)); raw=te.v1_risk_24m.to_numpy(float)
            fitted={}
            for c in candidates:
                a,loss=fit_alpha(xt,ty,tw,c['beta'],c['mode']); fitted[c['candidate']]=(a,loss); params.append({'candidate':c['candidate'],'beta':c['beta'],'mode':c['mode'],'alpha':a,'fit_objective':loss,'seed':seed,'outer_fold':fold})
                cand=sigmoid(a+c['beta']*xv); m=metrics(vy,vw,raw,cand); rank=bool(np.array_equal(np.argsort(raw,kind='mergesort'),np.argsort(cand,kind='mergesort'))); folds.append({'candidate':c['candidate'],'beta':c['beta'],'mode':c['mode'],'seed':seed,'outer_fold':fold,'rank_preserved':rank,**m}); pooled[c['candidate']].append((vy,vw,raw,cand))
                for pat,idx in te.groupby('acquisition_pattern',sort=True).groups.items():
                    idx=np.asarray(list(idx),int); patterns.append({'candidate':c['candidate'],'pattern':str(pat),**metrics(vy[idx],vw[idx],raw[idx],cand[idx])})
    fdf=pd.DataFrame(folds); pdf=pd.DataFrame(patterns); ptdf=pd.DataFrame(params); ag=[]
    for c in candidates:
        ys,ws,rs,cs=zip(*pooled[c['candidate']]); ag.append({'candidate':c['candidate'],'beta':c['beta'],'mode':c['mode'],**metrics(np.concatenate(ys),np.concatenate(ws),np.concatenate(rs),np.concatenate(cs)),'coverage':1.0,'rank_preservation_all_folds':bool(fdf.loc[fdf.candidate==c['candidate'],'rank_preserved'].all())})
    adf=pd.DataFrame(ag); pa=[]
    for (c,pat),g in pdf.groupby(['candidate','pattern'],sort=True):
        n=int(g.n_evaluable.sum()); e=int(g.events_evaluable.sum())
        if n==0: continue
        v=g.loc[g.n_evaluable>0]; rb=float(np.average(v.ipcw_brier_raw,weights=v.n_evaluable)); cb=float(np.average(v.ipcw_brier_candidate,weights=v.n_evaluable)); pa.append({'candidate':c,'pattern':pat,'n_evaluable':n,'events_evaluable':e,'ipcw_brier_raw':rb,'ipcw_brier_candidate':cb,'delta_ipcw_brier':cb-rb,'supported_pattern':bool(n>=20 and e>=5)})
    padf=pd.DataFrame(pa); safety=[]
    for _,r in adf.iterrows():
        pats=padf[(padf.candidate==r.candidate)&padf.supported_pattern]; worst=float(pats.delta_ipcw_brier.max()) if len(pats) else np.nan
        safety.append({'candidate':r.candidate,'beta':r.beta,'mode':r['mode'],'delta_ipcw_brier':r.delta_ipcw_brier,'worst_supported_pattern_regret':worst,'citl_candidate':r.citl_candidate,'slope_candidate':r.calibration_slope_candidate,'abs_citl_error_deterioration':r.abs_citl_error_deterioration,'abs_slope_error_deterioration':r.abs_slope_error_deterioration,'passes_brier_strict':bool(r.delta_ipcw_brier<=0.0005),'passes_pattern':bool(worst<=0.005) if np.isfinite(worst) else True,'citl_improved':bool(abs(r.citl_candidate)<abs(r.citl_raw)),'slope_improved':bool(abs(r.calibration_slope_candidate-1)<abs(r.calibration_slope_raw-1)),'rank_preserved':bool(r.rank_preservation_all_folds)})
    sdf=pd.DataFrame(safety); adf.to_csv(out/'citl_slope_balanced_aggregate_results.csv',index=False); fdf.to_csv(out/'citl_slope_balanced_fold_results.csv',index=False); padf.to_csv(out/'citl_slope_balanced_pattern_aggregate_results.csv',index=False); ptdf.to_csv(out/'citl_slope_balanced_parameters.csv',index=False); sdf.to_csv(out/'citl_slope_balanced_safety_screen.csv',index=False)
    summary={'analysis':'U5R6 rank-preserving fixed-slope bridge with Brier/log-loss intercept objective exploration','protocol':'frozen_citl_slope_balanced_bridge_exploration_protocol.yaml','candidate_count':len(candidates),'beta_grid':BETAS,'intercept_modes':MODES,'cohort':'HANCOCK official training development OOF','confirmation_evaluation_performed':False,'confirmation_outcomes_used_for_bridge_tuning':False,'patient_level_outputs':'not written','pareto_candidates':sdf.loc[sdf.passes_brier_strict&sdf.passes_pattern&sdf.citl_improved&sdf.slope_improved&sdf.rank_preserved].to_dict(orient='records')}
    (out/'citl_slope_balanced_exploration_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=='__main__': main()
