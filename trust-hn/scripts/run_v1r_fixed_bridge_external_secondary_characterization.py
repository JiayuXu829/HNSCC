from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
import run_v1r_beta09_logloss_bridge_confirmation_validation as bridge
from trust_hn.evaluation.phase6 import load_phase6_outcomes

HORIZON=730.5; REPS=2000; SEED=20260827; ALPHA=-0.14503379856995471; BETA=.90
COHORTS=("GSE65858","GSE41613")
PROTOCOL_REL=Path("research_studies/01_pattern_surv_hn/core_backbone/U5R10_fixed_bridge_external_secondary_characterization")
PARAM_REL=Path("research_studies/01_pattern_surv_hn/core_backbone/U5R7_V1R_beta09_logloss_bridge_candidate/selected_bridge_parameters.csv")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def safe(v):
    if isinstance(v,dict): return {str(k):safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [safe(x) for x in v]
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,float)): return float(v) if np.isfinite(v) else None
    if isinstance(v,(np.bool_,)): return bool(v)
    return v
def interval(values):
    x=np.asarray(values,float); x=x[np.isfinite(x)]
    return {"replicates":int(len(x)),"mean":float(x.mean()),"ci95_lower":float(np.quantile(x,.025)),"ci95_upper":float(np.quantile(x,.975))}
def main():
    root=Path(__file__).resolve().parents[1]; out=root/PROTOCOL_REL
    protocol_path=out/'frozen_u5r10_fixed_bridge_external_protocol.yaml'
    protocol=yaml.safe_load(protocol_path.read_text(encoding='utf-8-sig'))
    if protocol['status']!='FROZEN_BEFORE_EXECUTION': raise RuntimeError('protocol not frozen')
    pp=root/PARAM_REL; params=pd.read_csv(pp)
    if len(params)!=25 or not np.allclose(params.beta.astype(float),BETA): raise RuntimeError('bad frozen parameter artifact')
    if not np.isclose(float(params.alpha.mean()),ALPHA,atol=1e-15): raise RuntimeError('alpha mismatch')
    rows=[]; boots=[]; payload_cohorts={}
    for cohort in COHORTS:
        path=root/f"results/predictions/phase6/{cohort.lower()}__original__aggregate100.csv"
        p=pd.read_csv(path,dtype={'native_id':str}); expected=244 if cohort=='GSE65858' else 97
        if len(p)!=expected or 'b6_risk' not in p or 'b6_score' not in p: raise RuntimeError(f'prediction mismatch {cohort}')
        ids=p.native_id.astype(str).to_numpy(); o=load_phase6_outcomes(root,cohort,ids)
        raw=p.b6_risk.to_numpy(float); score=p.b6_score.to_numpy(float)
        transformed=bridge.sigmoid(ALPHA+BETA*bridge.logit(raw)); m=bridge.metrics(o.time,o.event,raw,transformed)
        rank_risk=bool(np.array_equal(np.argsort(np.argsort(raw)),np.argsort(np.argsort(transformed))))
        rank_score=bool(np.array_equal(np.argsort(np.argsort(score)),np.argsort(np.argsort(transformed))))
        row={'cohort':cohort,'n':len(p),'events':int(o.event.sum()),'coverage_raw':float(np.isfinite(raw).mean()),'coverage_bridge':float(np.isfinite(transformed).mean()),'base_definition':'legacy_phase6_B6_risk','alpha':ALPHA,'beta':BETA,'rank_preserved_risk':rank_risk,'rank_preserved_score':rank_score,**m}
        row.update({'passes_brier_nonharm_gate_0.0005':bool(m['delta_ipcw_brier']<=.0005),'calibration_citl_improved':bool(abs(m['citl_bridge'])<abs(m['citl_raw'])),'calibration_slope_improved':bool(m['abs_slope_error_change']<0)})
        row['all_directional_checks_pass']=bool(row['passes_brier_nonharm_gate_0.0005'] and row['calibration_citl_improved'] and row['calibration_slope_improved'] and rank_risk and row['coverage_raw']==row['coverage_bridge'])
        rows.append(row)
        rng=np.random.default_rng(SEED+(1 if cohort=='GSE65858' else 2)); ei=np.flatnonzero(o.event); ci=np.flatnonzero(~o.event); cb=[]
        for rep in range(REPS):
            sample=np.concatenate([rng.choice(ei,len(ei),replace=True),rng.choice(ci,len(ci),replace=True)]); rng.shuffle(sample)
            bm=bridge.metrics(o.time[sample],o.event[sample],raw[sample],transformed[sample]); br={'cohort':cohort,'replicate':rep+1}
            for k in ('delta_ipcw_brier','delta_citl','abs_citl_error_change','delta_calibration_slope','abs_slope_error_change'): br[k]=bm[k]
            boots.append(br); cb.append(br)
        payload_cohorts[cohort]={'prediction_file':str(path.relative_to(root)).replace('\\','/'),'prediction_file_sha256':sha(path),'point_estimate':row,'bootstrap':{k:interval([x[k] for x in cb]) for k in ('delta_ipcw_brier','delta_citl','abs_citl_error_change','delta_calibration_slope','abs_slope_error_change')}}
    rdf=pd.DataFrame(rows); bdf=pd.DataFrame(boots)
    payload={'schema_version':'0.1','stage_id':protocol['stage'],'evaluated_on':'2026-08-27','cohorts':payload_cohorts,'fixed_bridge':{'alpha':ALPHA,'beta':BETA,'parameter_source_sha256':sha(pp)},'bootstrap':{'method':'patient_level_stratified_bootstrap','replicates':REPS,'seed':SEED},'governance':{'outcomes_already_consumed_by_legacy_phase6':True,'parameters_refit_on_external_outcomes':False,'cohort_selected_after_readout':False,'current_v1r_prediction_modified':False,'router_trained':False,'patient_level_outputs_tracked':False,'current_v1r_external_confirmation_claim_permitted':False},'interpretation':{'external_direction_reproduced_on_legacy_b6':bool(rdf.all_directional_checks_pass.all()),'claim':'Fixed bridge calibration direction was reproduced on both GEO cohorts when applied to legacy Phase 6 B6 fusion risk; this is not current V1R bridge confirmation because prediction definitions are not proven equivalent.'}}
    (out/'u5r10_external_aggregate_results.json').write_text(json.dumps(safe(payload),indent=2,sort_keys=True)+'\n',encoding='utf-8'); rdf.to_csv(out/'u5r10_external_cohort_results.csv',index=False); bdf.to_csv(out/'u5r10_external_bootstrap_results.csv',index=False)
    audit='# U5R10 fixed bridge external secondary characterization audit\n\n- Protocol frozen before execution.\n- U5R7 alpha/beta were read from the pre-existing 25-fold development artifact; no external refit or candidate selection was performed.\n- Both available GEO cohorts were reported in full.\n- Outcomes were already consumed in historical Phase 6; this is locked post-unseal characterization, not pristine confirmation.\n- GEO files contain legacy Phase 6 B6 predictions, whose definition is not proven identical to current PATTERN-Surv-HN V1R.\n- The transform is strictly monotone; ranking and coverage were checked.\n\n## Claim boundary\n\nThe results support a reproducible calibration direction for the fixed bridge on legacy B6 transport characterization only. They do not establish current V1R bridge external validity. A genuine V1R confirmation requires a new outcome-untouched cohort and pre-outcome execution of the frozen V1R prediction contract.\n\n## Aggregate results\n\n```text\n'+rdf.to_string(index=False)+'\n```\n'
    (out/'u5r10_external_audit.md').write_text(audit,encoding='utf-8')
    hp=[protocol_path,pp,out/'u5r10_external_aggregate_results.json',out/'u5r10_external_cohort_results.csv',out/'u5r10_external_bootstrap_results.csv',out/'u5r10_external_audit.md']; hashes={str(x.relative_to(root)).replace('\\','/'):sha(x) for x in hp}; (out/'u5r10_external_hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(safe(payload),indent=2,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
