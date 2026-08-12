from __future__ import annotations
import csv, json, re
from pathlib import Path

HERE=Path(__file__).resolve(); ROOT=HERE.parents[3]
OUT=HERE.parents[1]/'project_management'/'evidence_map.csv'
H='730.5'
FIELDS='evidence_id phase analysis_nature dataset_code dataset_display_name dataset_role modality endpoint horizon_days model_or_comparison metric point_estimate ci_lower_95 ci_upper_95 parent_n evaluated_n events coverage source_file source_row ci_source_file ci_source_row claim_status allowed_claim_zh allowed_claim_en limitation_zh limitation_en planned_location planned_figure_or_table'.split()
DISPLAY={'RADCURE':'RADCURE','HANCOCK':'HANCOCK','TCGA-HNSC':'TCGA-HNSC','GSE65858':'GEO GSE65858','GSE41613':'GEO GSE41613','inner_hancock':'inner_hancock (known-overlap HANCOCK simulation)','PROJECT':'TRUST-HN governance'}
MOD={'RADCURE':'clinical; GTV; pretreatment CT radiomics','HANCOCK':'clinical/pathological; blood; TMA cell density','TCGA-HNSC':'clinical; RNA-seq transcriptomics','GSE65858':'clinical; microarray transcriptomics; cross-platform transfer','GSE41613':'microarray transcriptomics; HPV-negative OSCC sensitivity setting','inner_hancock':'HANCOCK-like clinical/pathological; blood; TMA features','PROJECT':'not applicable'}
CORE=['ipcw_brier','harrell_c','uno_c','auc_horizon','calibration_in_the_large','calibration_slope']
CI4=set(CORE[:4])
ZH={'ipcw_brier':'IPCW Brier评分','harrell_c':'Harrell C指数','uno_c':'Uno C指数','auc_horizon':'24个月AUC','calibration_in_the_large':'整体校准偏差','calibration_slope':'校准斜率','observed_coverage':'观察覆盖率'}
EN={'ipcw_brier':'IPCW Brier score','harrell_c':'Harrell C index','uno_c':'Uno C index','auc_horizon':'24-month AUC','calibration_in_the_large':'calibration-in-the-large','calibration_slope':'calibration slope','observed_coverage':'observed coverage'}

def read(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(enumerate(csv.DictReader(f),2))
def sl(s):return re.sub('[^A-Z0-9]+','-',s.upper()).strip('-')
def role(ds,phase):
    if ds=='RADCURE': return 'development/calibration ecosystem' if phase in {'Phase 2','Phase 4'} else 'prespecified locked retrospective test'
    if ds=='HANCOCK': return 'development/calibration ecosystem' if phase in {'Phase 2','Phase 4'} else 'prespecified retrospective OOD sealed test'
    return {'TCGA-HNSC':'transcriptomic development/calibration; no Phase 6 independent test','GSE65858':'prespecified retrospective external cross-platform test','GSE41613':'restricted retrospective sensitivity cohort (HPV-negative OSCC)','inner_hancock':'known-overlap workflow/bias simulation; not independent validation','PROJECT':'project governance'}[ds]
def nature(ds,phase):
    if phase=='Phase 4':return 'DEVELOPMENT_OR_CALIBRATION'
    if phase=='Phase 5':return 'DEVELOPMENT_STRESS_TEST'
    if phase=='Phase 7':return 'POST_HOC_EXPLORATORY'
    if phase=='Phase 8':return 'KNOWN_OVERLAP_SIMULATION_NOT_VALIDATION'
    if phase=='Governance':return 'GOVERNANCE_ANCHOR'
    return {'RADCURE':'PRESPECIFIED_LOCKED_RETROSPECTIVE','HANCOCK':'PRESPECIFIED_OOD_RETROSPECTIVE','GSE65858':'PRESPECIFIED_EXTERNAL_RETROSPECTIVE','GSE41613':'RESTRICTED_SENSITIVITY_ANALYSIS'}.get(ds,'COHORT_DEFINITION')
def status(ds,phase,kind=''):
    if phase in {'Phase 4','Phase 5'}:return 'DEVELOPMENT_ONLY'
    if phase=='Phase 7':return 'POST_HOC_EXPLORATORY_ONLY'
    if phase=='Phase 8':return 'OVERLAP_SIMULATION_ONLY_NOT_VALIDATION'
    if ds=='GSE41613':return 'SENSITIVITY_ONLY'
    if kind=='dca':return 'EXPLORATORY_NO_CLINICAL_UTILITY'
    if kind=='negative':return 'ALLOWED_NEGATIVE_RESULT_NO_MODALITY_SPECIFICITY'
    if phase=='Governance':return 'GOVERNANCE_BOUNDARY'
    return 'ALLOWED_WITH_ROLE_QUALIFIER'
def place(phase,kind=''):
    if phase=='Phase 2':return 'Methods/Results cohort flow','WP4 candidate Figure 2 or Table 1'
    if phase=='Phase 4':return 'Results development; detail in Supplement','WP4 candidate Figure 3 / supplementary tables'
    if phase=='Phase 5':return 'Results limitations; detail in Supplement','WP4 candidate Table 4 / stress-test supplement'
    if phase=='Phase 6':
        return ({'paired':('Results locked/external comparisons','WP4 candidate Figure 4 and Table 3'),'action':('Results reliability gating','WP4 candidate Figure 5 and Table 4'),'negative':('Results negative controls','WP4 candidate Figure 6/7 and Supplement'),'dca':('Exploratory DCA; threshold detail in Supplement','WP4 candidate supplementary figure/table')}.get(kind,('Results absolute performance','WP4 candidate Table 2')))
    if phase=='Phase 7':return 'Results post hoc exploratory comparators','WP4 candidate comparator panel / Supplement'
    if phase=='Phase 8':return 'Supplement only: overlap/bias simulation','WP4 candidate Phase 8 supplementary panel'
    return 'Methods/governance','No efficacy figure'
def base(ds,phase,kind=''):
    a,b=place(phase,kind);return dict(phase=phase,analysis_nature=nature(ds,phase),dataset_code=ds,dataset_display_name=DISPLAY[ds],dataset_role=role(ds,phase),modality=MOD[ds],endpoint='24-month overall survival' if ds!='PROJECT' else 'not applicable',horizon_days=H if ds!='PROJECT' else '',claim_status=status(ds,phase,kind),planned_location=a,planned_figure_or_table=b)
def lim(ds,phase,kind='',b7=False):
    z=[];e=[]
    if phase=='Phase 4':z+=['仅为开发/校准证据，无患者级bootstrap 95%CI，不支持独立验证。'];e+=['Development/calibration evidence only, without patient-level bootstrap 95% CIs; not independent validation.']
    if phase=='Phase 5':z+=['仅为开发阶段压力测试，不能证明所有分布偏移下普遍稳健。'];e+=['Development stress testing only; it cannot establish universal shift robustness.']
    if phase=='Phase 7':z+=['必须明确标为post hoc exploratory，不得写成预设锁定比较。'];e+=['Must be labelled post hoc exploratory, not a prespecified locked comparison.']
    if phase=='Phase 8':z+=['包含88例训练、17例校准及30例既往测试重叠，不得作为独立院内验证。'];e+=['Includes 88 training-, 17 calibration-, and 30 prior-test-overlap cases; not independent institutional validation.']
    if ds=='GSE41613':z+=['仅为HPV阴性OSCC敏感性分析，不是一般HNSCC外部验证。'];e+=['HPV-negative OSCC sensitivity analysis only; not general HNSCC external validation.']
    if ds=='GSE65858':z+=['跨RNA-seq/微阵列平台转移，必须同时呈现校准失败。'];e+=['Cross-platform RNA-seq/microarray transfer; calibration failure must be reported.']
    if b7:z+=['B7必须同时报告覆盖率，并在相同非弃权患者子集比较。'];e+=['B7 requires coverage and identical non-abstained-subset comparisons.']
    if kind=='dca':z+=['回顾性探索性DCA不支持临床效用、净获益或患者获益声明。'];e+=['Retrospective exploratory DCA does not establish clinical utility or patient benefit.']
    if kind=='negative':z+=['不得据此声称放射组学特异性生物学信号。'];e+=['No radiomics-specific biological-signal claim is supported.']
    return ' '.join(z),' '.join(e)
def add(out,**kw):
    r={x:'' for x in FIELDS};r.update({k:str(v) if v is not None else '' for k,v in kw.items()});out.append(r)
def claim(ds,model,metric,val,phase,cov='',ci=None):
    prezh='事后探索性分析中，' if phase=='Phase 7' else ('已知重叠模拟中，' if phase=='Phase 8' else '')
    preen='In the post hoc exploratory analysis, ' if phase=='Phase 7' else ('In the known-overlap simulation, ' if phase=='Phase 8' else '')
    cz=f'（95%CI {ci[0]}至{ci[1]}）' if ci and all(ci) else '';ce=f' (95% CI {ci[0]} to {ci[1]})' if ci and all(ci) else ''
    vz=f'，覆盖率为{cov}' if model.startswith('B7') and cov else '';ve=f', with coverage {cov}' if model.startswith('B7') and cov else ''
    return f'{prezh}{ds}中{model}的{ZH.get(metric,metric)}为{val}{cz}{vz}。',f'{preen}{model} had {EN.get(metric,metric)} {val}{ce} in {ds}{ve}.'

def build():
    out=[]
    p='results/metrics/phase2/cohort_flow.csv'
    for line,s in read(p):
        ds=s['study'];z,e=lim(ds,'Phase 2');b=base(ds,'Phase 2');b['analysis_nature']='COHORT_DEFINITION'
        if s['flow_step']=='analysis_split':
            b['dataset_role']={'train':'development training split','calibration':'development calibration split','sealed_test':('prespecified locked retrospective test' if ds=='RADCURE' else 'prespecified retrospective OOD sealed test'),'external_test':'prespecified retrospective external test','sensitivity':'restricted retrospective sensitivity cohort'}[s['category']]
        else:b['dataset_role']='cohort source/eligibility/exclusion accounting before analysis-role assignment'
        add(out,**b,evidence_id=f'P2-FLOW-R{line:03}',model_or_comparison=f"{s['flow_step']}:{s['category']}",metric='cohort_flow_n',point_estimate=s['n'],parent_n=s['n'],evaluated_n=s['n'],source_file=p,source_row=line,allowed_claim_zh=f"{ds}队列流程步骤“{s['flow_step']} / {s['category']}”人数为{s['n']}。",allowed_claim_en=f"The {ds} cohort-flow step '{s['flow_step']} / {s['category']}' contained {s['n']} records.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase4/model_metrics.csv'
    for line,s in read(p):
        for m in CORE:
            z,e=lim(s['study'],'Phase 4');cz,ce=claim(s['study'],s['model'],m,s[m],'Phase 4')
            add(out,**base(s['study'],'Phase 4'),evidence_id=f'P4-MODEL-R{line:03}-{sl(m)}',model_or_comparison=f"{s['model']}; seed={s['seed']}; partition={s['partition']}",metric=m,point_estimate=s[m],evaluated_n=s['n'],events=s['events'],source_file=p,source_row=line,allowed_claim_zh=cz,allowed_claim_en=ce,limitation_zh=z,limitation_en=e)
    p='results/metrics/phase4/gate_metrics.csv'
    for line,s in read(p):
        for m in CORE+['observed_coverage']:
            z,e=lim(s['study'],'Phase 4',b7=True);cz,ce=claim(s['study'],s['model'],m,s[m],'Phase 4',s['observed_coverage'])
            add(out,**base(s['study'],'Phase 4'),evidence_id=f'P4-GATE-R{line:03}-{sl(m)}',model_or_comparison=f"{s['model']}; seed={s['seed']}; partition={s['partition']}; profile={s['profile']}",metric=m,point_estimate=s[m],evaluated_n=s['n'],events=s['events'],coverage=s['observed_coverage'],source_file=p,source_row=line,allowed_claim_zh=cz,allowed_claim_en=ce,limitation_zh=z,limitation_en=e)
    p='results/metrics/phase4/action_summary.csv';a4=read(p);tot4={}
    for _,s in a4:tot4[(s['study'],s['partition'],s['seed'],s['profile'])]=tot4.get((s['study'],s['partition'],s['seed'],s['profile']),0)+int(s['count'])
    for line,s in a4:
        z,e=lim(s['study'],'Phase 4',b7=True)
        add(out,**base(s['study'],'Phase 4'),evidence_id=f'P4-ACTION-R{line:03}',model_or_comparison=f"B7-{s['profile']}; seed={s['seed']}; partition={s['partition']}; action={s['action']}",metric='action_rate',point_estimate=s['rate'],parent_n=tot4[(s['study'],s['partition'],s['seed'],s['profile'])],evaluated_n=tot4[(s['study'],s['partition'],s['seed'],s['profile'])],coverage=s['non_abstention_coverage'],source_file=p,source_row=line,allowed_claim_zh=f"开发/校准分析中，{s['study']}的B7-{s['profile']}在{s['partition']}分区种子{s['seed']}下，{s['action']}比例为{s['rate']}，非弃权覆盖率{s['non_abstention_coverage']}。",allowed_claim_en=f"In development/calibration, B7-{s['profile']} produced an {s['action']} rate of {s['rate']} in {s['study']} {s['partition']} for seed {s['seed']}, with coverage {s['non_abstention_coverage']}.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase5/acceptance_checks.csv'
    for line,s in read(p):
        z,e=lim(s['study'],'Phase 5');ok=s['passed'].lower()=='true'
        add(out,**base(s['study'],'Phase 5'),evidence_id=f'P5-CHECK-R{line:03}',model_or_comparison=s['check'],metric='acceptance_check_value',point_estimate=s['value'],source_file=p,source_row=line,allowed_claim_zh=f"{s['study']}压力测试检查“{s['check']}”值为{s['value']}，标准{s['criterion']}，结果{'通过' if ok else '未通过'}。",allowed_claim_en=f"The {s['study']} stress-test check '{s['check']}' had value {s['value']} against {s['criterion']} and {'passed' if ok else 'failed'}.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase5/model_status.csv'
    for line,s in read(p):
        z,e=lim(s['study'],'Phase 5')
        add(out,**base(s['study'],'Phase 5'),evidence_id=f'P5-STATUS-R{line:03}',model_or_comparison=f"seed={s['seed'] or 'NA'}",metric='model_run_status',point_estimate=s['status'],source_file=p,source_row=line,allowed_claim_zh=f"Phase 5中{s['study']}种子{s['seed'] or '不适用'}状态为{s['status']}；原因：{s['reason'] or '无'}。",allowed_claim_en=f"In Phase 5, {s['study']} seed {s['seed'] or 'NA'} had status {s['status']}; reason: {s['reason'] or 'none'}.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase5/worst_group_regret.csv'
    for line,s in read(p):
        if s['flagged'].lower()!='true':continue
        z,e=lim(s['study'],'Phase 5',b7=True)
        add(out,**base(s['study'],'Phase 5'),evidence_id=f'P5-FLAG-R{line:03}',model_or_comparison=f"B7 vs B2; seed={s['seed']}; {s['subgroup_variable']}={s['subgroup']}",metric='brier_regret_vs_b2',point_estimate=s['brier_regret_vs_b2'],parent_n=s['parent_n'],coverage=s['coverage'],source_file=p,source_row=line,allowed_claim_zh=f"探索性最差亚组审计中，{s['study']}种子{s['seed']}的{s['subgroup_variable']}={s['subgroup']}被标记，Brier regret为{s['brier_regret_vs_b2']}，覆盖率{s['coverage']}。",allowed_claim_en=f"The exploratory worst-group audit flagged {s['study']} seed {s['seed']} {s['subgroup_variable']}={s['subgroup']}, with Brier regret {s['brier_regret_vs_b2']} and coverage {s['coverage']}.",limitation_zh=z,limitation_en=e)
    cip='results/metrics/phase6/bootstrap_confidence_intervals.csv';ci={(s['cohort'],s['model'],s['metric']):(n,s) for n,s in read(cip)}
    p='results/metrics/phase6/cohort_metrics.csv';abs6=read(p);cov6={s['cohort']:s['coverage'] for _,s in abs6 if s['model']=='B7'};parent6={s['cohort']:s['parent_n'] for _,s in abs6}
    for line,s in abs6:
        for m in CORE:
            cn,c=ci.get((s['cohort'],s['model'],m),('',{}));pair=(c.get('ci_lower_95',''),c.get('ci_upper_95','')) if c else None
            z,e=lim(s['cohort'],'Phase 6',b7=s['model']=='B7');cz,ce=claim(s['cohort'],s['model'],m,s[m],'Phase 6',s['coverage'],pair)
            add(out,**base(s['cohort'],'Phase 6'),evidence_id=f'P6-ABS-R{line:03}-{sl(m)}',model_or_comparison=s['model'],metric=m,point_estimate=s[m],ci_lower_95=c.get('ci_lower_95',''),ci_upper_95=c.get('ci_upper_95',''),parent_n=s['parent_n'],evaluated_n=s['n'],events=s['events'],coverage=s['coverage'],source_file=p,source_row=line,ci_source_file=cip if c else '',ci_source_row=cn,allowed_claim_zh=cz,allowed_claim_en=ce,limitation_zh=z,limitation_en=e)
    p='results/metrics/phase6/paired_comparisons.csv'
    for line,s in read(p):
        b7='B7' in s['comparison'];cov=cov6.get(s['cohort'],'') if b7 else '1.0';z,e=lim(s['cohort'],'Phase 6',b7=b7)
        add(out,**base(s['cohort'],'Phase 6','paired'),evidence_id=f'P6-PAIR-R{line:03}',model_or_comparison=s['comparison'],metric=s['metric'],point_estimate=s['point_estimate'],ci_lower_95=s['ci_lower_95'],ci_upper_95=s['ci_upper_95'],parent_n=parent6[s['cohort']],evaluated_n=s['n'],coverage=cov,source_file=p,source_row=line,ci_source_file=p,ci_source_row=line,allowed_claim_zh=f"{s['cohort']}中{s['comparison']}在相同{s['n']}例子集上的{s['metric']}差值为{s['point_estimate']}（95%CI {s['ci_lower_95']}至{s['ci_upper_95']}）"+(f"，B7覆盖率{cov}。" if b7 else '。'),allowed_claim_en=f"In {s['cohort']}, {s['comparison']} had {s['metric']} difference {s['point_estimate']} (95% CI {s['ci_lower_95']} to {s['ci_upper_95']}) on the identical {s['n']}-patient subset"+(f", with B7 coverage {cov}." if b7 else '.'),limitation_zh=z+' Brier差值为负有利于前列模型；辨别指标差值为正有利于前列模型。',limitation_en=e+' Negative Brier differences favor the first-listed model; positive discrimination differences favor it.')
    p='results/metrics/phase6/action_summary.csv';a6=read(p);tot6={}
    for _,s in a6:tot6[(s['cohort'],s['gate_profile'])]=tot6.get((s['cohort'],s['gate_profile']),0)+int(s['count'])
    for line,s in a6:
        z,e=lim(s['cohort'],'Phase 6',b7=True)
        add(out,**base(s['cohort'],'Phase 6','action'),evidence_id=f'P6-ACTION-R{line:03}',model_or_comparison=f"B7 profile={s['gate_profile']}; action={s['action']}",metric='action_rate',point_estimate=s['rate'],parent_n=tot6[(s['cohort'],s['gate_profile'])],evaluated_n=tot6[(s['cohort'],s['gate_profile'])],coverage=s['non_abstention_coverage'],source_file=p,source_row=line,allowed_claim_zh=f"{s['cohort']}的B7方案{s['gate_profile']}产生{s['action']}动作{s['count']}例（比例{s['rate']}），非弃权覆盖率{s['non_abstention_coverage']}。",allowed_claim_en=f"For {s['cohort']}, B7 profile {s['gate_profile']} produced {s['count']} {s['action']} actions (rate {s['rate']}), with coverage {s['non_abstention_coverage']}.",limitation_zh=z+' 动作不是治疗建议。',limitation_en=e+' Gate actions are not treatment recommendations.')
    p='results/metrics/phase6/radcure_negative_controls.csv'
    for line,s in read(p):
        if s['row_type']=='assay_metric':
            for m in CORE[:4]:
                z,e=lim('RADCURE','Phase 6','negative',s['model']=='B7')
                add(out,**base('RADCURE','Phase 6','negative'),evidence_id=f'P6-NEG-ABS-R{line:03}-{sl(m)}',model_or_comparison=f"assay={s['assay']}; model={s['model']}",metric=m,point_estimate=s[m],parent_n=s['parent_n'],evaluated_n=s['n'],events=s['events'],coverage=s['coverage'],source_file=p,source_row=line,allowed_claim_zh=f"RADCURE负对照中，{s['assay']} assay的{s['model']}之{ZH[m]}为{s[m]}。",allowed_claim_en=f"In RADCURE negative controls, {s['model']} under {s['assay']} had {EN[m]} {s[m]}.",limitation_zh=z,limitation_en=e)
        else:
            z,e=lim('RADCURE','Phase 6','negative',s['model']=='B7');cov=cov6['RADCURE'] if s['model']=='B7' else '1.0'
            add(out,**base('RADCURE','Phase 6','negative'),evidence_id=f'P6-NEG-PAIR-R{line:03}',model_or_comparison=f"{s['model']}: {s['reference_assay']} vs {s['control_assay']}",metric=s['metric'],point_estimate=s['point_estimate'],ci_lower_95=s['ci_lower_95'],ci_upper_95=s['ci_upper_95'],parent_n=parent6['RADCURE'],evaluated_n=s['comparison_n'],coverage=cov,source_file=p,source_row=line,ci_source_file=p,ci_source_row=line,allowed_claim_zh=f"RADCURE中{s['model']}的{s['reference_assay']}减{s['control_assay']}之{s['metric']}差值为{s['point_estimate']}（95%CI {s['ci_lower_95']}至{s['ci_upper_95']}）。",allowed_claim_en=f"For {s['model']} in RADCURE, {s['reference_assay']}-minus-{s['control_assay']} {s['metric']} was {s['point_estimate']} (95% CI {s['ci_lower_95']} to {s['ci_upper_95']}).",limitation_zh=z,limitation_en=e)
    sizes6={s['cohort']:(s['parent_n'],s['n']) for _,s in abs6 if s['model']=='B7'}
    p='results/metrics/phase6/decision_curve.csv'
    for line,s in read(p):
        z,e=lim(s['cohort'],'Phase 6','dca',s['model']=='B7');cov=cov6[s['cohort']] if s['model']=='B7' else '1.0'
        add(out,**base(s['cohort'],'Phase 6','dca'),evidence_id=f'P6-DCA-R{line:03}',model_or_comparison=f"{s['model']}; threshold={s['threshold']}",metric='net_benefit_model',point_estimate=s['net_benefit_model'],parent_n=sizes6[s['cohort']][0],evaluated_n=(sizes6[s['cohort']][1] if s['model']=='B7' else sizes6[s['cohort']][0]),coverage=cov,source_file=p,source_row=line,allowed_claim_zh=f"探索性DCA中，{s['cohort']}的{s['model']}在阈值{s['threshold']}处净获益{s['net_benefit_model']}（treat-all={s['net_benefit_all']}）。",allowed_claim_en=f"In exploratory DCA, {s['model']} in {s['cohort']} had net benefit {s['net_benefit_model']} at threshold {s['threshold']} (treat-all={s['net_benefit_all']}).",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase7_exploratory/development_metrics_summary.csv'
    for line,s in read(p):
        for m in CORE:
            v=s[m+'_mean'];sd=s[m+'_sd'];z,e=lim(s['study'],'Phase 7');cz,ce=claim(s['study'],s['model'],m,v,'Phase 7')
            add(out,**base(s['study'],'Phase 7'),evidence_id=f'P7-DEV-R{line:03}-{sl(m)}',model_or_comparison=f"{s['model']}; partition={s['partition']}; five-seed summary",metric=m,point_estimate=v,source_file=p,source_row=line,allowed_claim_zh=cz[:-1]+f"，{s['seeds']}个种子的SD为{sd}。",allowed_claim_en=ce[:-1]+f", with SD {sd} across {s['seeds']} seeds.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase7_exploratory/external_metrics.csv'
    for line,s in read(p):
        for m in CORE:
            z,e=lim(s['cohort'],'Phase 7');cz,ce=claim(s['cohort'],s['model'],m,s[m],'Phase 7',s['coverage'])
            add(out,**base(s['cohort'],'Phase 7'),evidence_id=f'P7-EXT-R{line:03}-{sl(m)}',model_or_comparison=s['model'],metric=m,point_estimate=s[m],evaluated_n=s['n'],events=s['events'],coverage=s['coverage'],source_file=p,source_row=line,allowed_claim_zh=cz,allowed_claim_en=ce,limitation_zh=z+' 绝对指标表无bootstrap 95%CI；推断比较使用配对表。',limitation_en=e+' Absolute metrics lack bootstrap 95% CIs; use paired comparisons for inference.')
    p='results/metrics/phase7_exploratory/paired_comparisons.csv';n7={'RADCURE':'626','HANCOCK':'152','GSE65858':'244','GSE41613':'97'}
    for line,s in read(p):
        z,e=lim(s['cohort'],'Phase 7')
        add(out,**base(s['cohort'],'Phase 7'),evidence_id=f'P7-PAIR-R{line:03}',model_or_comparison=s['comparison'],metric=s['metric'],point_estimate=s['point_estimate'],ci_lower_95=s['ci_lower_95'],ci_upper_95=s['ci_upper_95'],parent_n=n7[s['cohort']],evaluated_n=n7[s['cohort']],coverage='1.0',source_file=p,source_row=line,ci_source_file=p,ci_source_row=line,allowed_claim_zh=f"事后探索性分析中，{s['cohort']}的{s['comparison']}之{s['metric']}差值为{s['point_estimate']}（95%CI {s['ci_lower_95']}至{s['ci_upper_95']}）。",allowed_claim_en=f"Post hoc exploratorily, {s['comparison']} in {s['cohort']} had {s['metric']} difference {s['point_estimate']} (95% CI {s['ci_lower_95']} to {s['ci_upper_95']}).",limitation_zh=z+' Brier差值为负有利于前列模型；辨别指标差值为正有利于前列模型。',limitation_en=e+' Negative Brier differences favor the first-listed model; positive discrimination differences favor it.')
    cip='results/metrics/phase8_pseudo_private/bootstrap_confidence_intervals.csv';ci8={(s['model'],s['metric']):(n,s) for n,s in read(cip)}
    p='results/metrics/phase8_pseudo_private/model_metrics.csv';abs8=read(p);cov8=next(s['coverage'] for _,s in abs8 if s['model']=='B7');parent8=next(s['parent_n'] for _,s in abs8 if s['model']=='B7')
    for line,s in abs8:
        for m in CORE:
            cn,c=ci8.get((s['model'],m),('',{}));pair=(c.get('ci_lower_95',''),c.get('ci_upper_95','')) if c else None;z,e=lim('inner_hancock','Phase 8',b7=s['model']=='B7');cz,ce=claim('inner_hancock',s['model'],m,s[m],'Phase 8',s['coverage'],pair)
            add(out,**base('inner_hancock','Phase 8'),evidence_id=f'P8-ABS-R{line:03}-{sl(m)}',model_or_comparison=s['model'],metric=m,point_estimate=s[m],ci_lower_95=c.get('ci_lower_95',''),ci_upper_95=c.get('ci_upper_95',''),parent_n=s['parent_n'],evaluated_n=s['n'],events=s['events'],coverage=s['coverage'],source_file=p,source_row=line,ci_source_file=cip if c else '',ci_source_row=cn,allowed_claim_zh=cz,allowed_claim_en=ce,limitation_zh=z,limitation_en=e)
    p='results/metrics/phase8_pseudo_private/paired_comparisons.csv'
    for line,s in read(p):
        b7='B7' in s['comparison'];z,e=lim('inner_hancock','Phase 8',b7=b7)
        add(out,**base('inner_hancock','Phase 8'),evidence_id=f'P8-PAIR-R{line:03}',model_or_comparison=s['comparison'],metric=s['metric'],point_estimate=s['point_difference'],ci_lower_95=s['ci_lower_95'],ci_upper_95=s['ci_upper_95'],parent_n=parent8,evaluated_n=s['common_subset_n'],coverage=cov8 if b7 else '1.0',source_file=p,source_row=line,ci_source_file=p,ci_source_row=line,allowed_claim_zh=f"已知重叠模拟中，{s['comparison']}在共同{s['common_subset_n']}例上的{s['metric']}差值为{s['point_difference']}（95%CI {s['ci_lower_95']}至{s['ci_upper_95']}）。",allowed_claim_en=f"In the known-overlap simulation, {s['comparison']} had {s['metric']} difference {s['point_difference']} (95% CI {s['ci_lower_95']} to {s['ci_upper_95']}) in {s['common_subset_n']} common cases.",limitation_zh=z,limitation_en=e)
    p='results/metrics/phase8_pseudo_private/action_summary.csv';a8=read(p);tot8=sum(int(s['count']) for _,s in a8)
    for line,s in a8:
        z,e=lim('inner_hancock','Phase 8',b7=True)
        add(out,**base('inner_hancock','Phase 8'),evidence_id=f'P8-ACTION-R{line:03}',model_or_comparison=f"B7; action={s['action']}",metric='action_rate',point_estimate=s['rate'],parent_n=tot8,evaluated_n=tot8,coverage=s['non_abstention_coverage'],source_file=p,source_row=line,allowed_claim_zh=f"已知重叠模拟中，B7产生{s['action']}动作{s['count']}例（比例{s['rate']}），覆盖率{s['non_abstention_coverage']}。",allowed_claim_en=f"In the known-overlap simulation, B7 produced {s['count']} {s['action']} actions (rate {s['rate']}), with coverage {s['non_abstention_coverage']}.",limitation_zh=z+' 动作不是治疗建议。',limitation_en=e+' Gate actions are not treatment recommendations.')
    anchors=[('configs/analysis_freeze.yaml','$.status','analysis_freeze_status','FROZEN'),('configs/analysis_freeze.yaml','$.primary_gate','prespecified_primary_gate','full_equal_weight_90'),('configs/analysis_freeze.yaml','$.phase6_outcome_access_state','phase6_outcome_access_state','CONSUMED_FOR_LOCKED_EVALUATION'),('results/manifests/phase6_locked_evaluation_receipt.json','$.bootstrap_replicates','phase6_bootstrap_replicates','2000'),('configs/phase7_exploratory_benchmarks.json','$.analysis_label','phase7_analysis_label','post hoc exploratory benchmark'),('configs/phase7_exploratory_benchmarks.json','$.governance.prespecified_locked_comparison','phase7_prespecified_locked_comparison','False'),('configs/phase8_pseudo_private_overlap_simulation.json','$.known_cohort_overlap','phase8_known_cohort_overlap','True'),('configs/phase8_pseudo_private_overlap_simulation.json','$.independent_private_validation','phase8_independent_private_validation','False'),('configs/phase8_pseudo_private_overlap_simulation.json','$.source_partition_composition.train','phase8_train_overlap_n','88'),('configs/phase8_pseudo_private_overlap_simulation.json','$.source_partition_composition.calibration','phase8_calibration_overlap_n','17'),('configs/phase8_pseudo_private_overlap_simulation.json','$.source_partition_composition.sealed_test','phase8_sealed_test_overlap_n','30')]
    for i,(p,loc,m,expected) in enumerate(anchors,1):
        v=json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
        for k in loc[2:].split('.'):v=v[k]
        assert str(v)==expected,(p,loc,v,expected)
        add(out,**base('PROJECT','Governance'),evidence_id=f'GOV-ANCHOR-{i:03}',model_or_comparison='governance boundary',metric=m,point_estimate=v,source_file=p,source_row=loc,allowed_claim_zh=f'治理记录显示{m}={v}。',allowed_claim_en=f'The governance record specifies {m}={v}.',limitation_zh='只界定分析和写作边界，不是模型有效性证据。',limitation_en='Defines analysis/reporting boundaries; not model-validity evidence.')
    return out

def main():
    rows=build();OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
    pc={};sc={}
    for r in rows:pc[r['phase']]=pc.get(r['phase'],0)+1;sc[r['claim_status']]=sc.get(r['claim_status'],0)+1
    print(f'wrote {len(rows)} rows to {OUT}');print('phase_counts='+json.dumps(pc,ensure_ascii=False,sort_keys=True));print('status_counts='+json.dumps(sc,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
