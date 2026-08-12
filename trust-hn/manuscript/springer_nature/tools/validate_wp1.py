from __future__ import annotations
import csv, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve();ROOT=HERE.parents[3]
MAP=HERE.parents[1]/'project_management'/'evidence_map.csv'
REQUIRED='evidence_id phase analysis_nature dataset_code dataset_display_name dataset_role modality endpoint horizon_days model_or_comparison metric point_estimate ci_lower_95 ci_upper_95 parent_n evaluated_n events coverage source_file source_row ci_source_file ci_source_row claim_status allowed_claim_zh allowed_claim_en limitation_zh limitation_en planned_location planned_figure_or_table'.split()

def fail(errors,msg): errors.append(msg)
def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def resolve_jsonpath(obj,loc):
    if not loc.startswith('$.'):raise ValueError('not JSONPath')
    cur=obj
    for key in loc[2:].split('.'):cur=cur[key]
    return cur
def eq(a,b):
    try:return abs(float(a)-float(b))<=1e-12
    except (ValueError,TypeError):return str(a).lower()==str(b).lower()
def expected_value(source,metric):
    if metric in source:return source[metric]
    aliases={'cohort_flow_n':'n','action_rate':'rate','acceptance_check_value':'value','model_run_status':'status','brier_regret_vs_b2':'brier_regret_vs_b2','net_benefit_model':'net_benefit_model'}
    if metric in aliases:return source.get(aliases[metric])
    if metric+'_mean' in source:return source[metric+'_mean']
    return None

def main():
    errors=[];warnings=[]
    if not MAP.exists():fail(errors,f'missing {MAP}');return finish(errors,warnings,0)
    rows=csv_rows(MAP)
    if not rows:fail(errors,'evidence map is empty');return finish(errors,warnings,0)
    if list(rows[0])!=REQUIRED:fail(errors,'header differs from required WP1 schema')
    ids=[r['evidence_id'] for r in rows]
    if len(ids)!=len(set(ids)):fail(errors,'evidence_id values are not unique')
    if len(rows)<1500:warnings.append(f'row count {len(rows)} is below the planned comprehensive range')
    source_cache={};json_cache={}
    for i,r in enumerate(rows,2):
        tag=f"map row {i} ({r['evidence_id']})"
        src=ROOT/r['source_file']
        if not src.is_file():fail(errors,f'{tag}: source missing: {r["source_file"]}');continue
        loc=r['source_row']
        if src.suffix.lower()=='.csv':
            if not loc.isdigit():fail(errors,f'{tag}: CSV source_row is not numeric: {loc}');continue
            data=source_cache.setdefault(str(src),csv_rows(src));idx=int(loc)-2
            if idx<0 or idx>=len(data):fail(errors,f'{tag}: source_row {loc} out of range');continue
            source_row=data[idx]
            expected=expected_value(source_row,r['metric'])
            if expected not in (None,'') and r['point_estimate']!='' and not eq(expected,r['point_estimate']):fail(errors,f'{tag}: point estimate does not match source row ({expected} != {r["point_estimate"]})')
            if r['metric']=='action_rate':
                if not r['parent_n'] or not r['evaluated_n']:
                    fail(errors,f'{tag}: action rate lacks denominator fields')
                else:
                    try:
                        denominator=float(r['evaluated_n']);count=float(source_row['count']);rate=float(r['point_estimate'])
                        if not eq(r['parent_n'],r['evaluated_n']):fail(errors,f'{tag}: action-rate parent_n and evaluated_n differ')
                        if abs(rate*denominator-count)>1e-8:fail(errors,f'{tag}: action count/rate/denominator are inconsistent')
                    except (KeyError,ValueError,TypeError) as exc:fail(errors,f'{tag}: invalid action-rate denominator data: {exc}')
        else:
            try:
                obj=json_cache.setdefault(str(src),json.loads(src.read_text(encoding='utf-8-sig')))
                value=resolve_jsonpath(obj,loc)
                if not eq(value,r['point_estimate']):fail(errors,f'{tag}: JSONPath value mismatch ({value} != {r["point_estimate"]})')
            except Exception as exc:fail(errors,f'{tag}: invalid JSON locator {loc}: {exc}')
        lo,hi=r['ci_lower_95'],r['ci_upper_95']
        if bool(lo)!=bool(hi):fail(errors,f'{tag}: incomplete 95% CI')
        if lo and hi:
            try:
                if float(lo)>float(hi):fail(errors,f'{tag}: CI lower > upper')
            except ValueError:fail(errors,f'{tag}: nonnumeric CI')
            if not r['ci_source_file'] or not r['ci_source_row']:fail(errors,f'{tag}: CI is present without CI source locator')
        if r['ci_source_file']:
            cp=ROOT/r['ci_source_file']
            if not cp.is_file():fail(errors,f'{tag}: CI source missing')
            elif cp.suffix.lower()=='.csv':
                if not r['ci_source_row'].isdigit():fail(errors,f'{tag}: CI CSV row is not numeric')
                else:
                    cr=source_cache.setdefault(str(cp),csv_rows(cp));j=int(r['ci_source_row'])-2
                    if j<0 or j>=len(cr):fail(errors,f'{tag}: CI source row out of range')
        if r['phase']=='Phase 7' and r['claim_status']!='POST_HOC_EXPLORATORY_ONLY':fail(errors,f'{tag}: Phase 7 status is not post hoc exploratory only')
        if r['phase']=='Phase 8' and r['claim_status']!='OVERLAP_SIMULATION_ONLY_NOT_VALIDATION':fail(errors,f'{tag}: Phase 8 status is not overlap-simulation only')
        if r['dataset_code']=='GSE41613' and 'sensitivity' not in (r['dataset_role']+' '+r['limitation_en']).lower():fail(errors,f'{tag}: GSE41613 lacks sensitivity-only boundary')
        if r['phase']=='Phase 6' and 'B7' in r['model_or_comparison']:
            if not r['coverage']:fail(errors,f'{tag}: Phase 6 B7 evidence lacks coverage')
            if '_vs_' in r['model_or_comparison'] and 'identical' not in r['allowed_claim_en'].lower():fail(errors,f'{tag}: B7 paired comparison lacks identical-subset wording')
        if r['metric']=='net_benefit_model' and not any(x in r['limitation_en'].lower() for x in ['does not establish clinical utility','not establish clinical utility']):fail(errors,f'{tag}: DCA lacks no-clinical-utility boundary')
        if r['claim_status']=='ALLOWED_NEGATIVE_RESULT_NO_MODALITY_SPECIFICITY' and 'radiomics-specific' not in r['limitation_en'].lower():fail(errors,f'{tag}: negative control lacks modality-specificity prohibition')
    prohibited=['prospective validation','patient benefit','deployable threshold','universal robustness','independent institutional validation']
    for i,r in enumerate(rows,2):
        text=r['allowed_claim_en'].lower()
        for phrase in prohibited:
            if phrase in text and not any(x in text for x in ['not ','cannot ','no ']):fail(errors,f'map row {i}: allowed claim may assert prohibited phrase {phrase!r}')
    try:
        top=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True,capture_output=True,check=True)
        git_root=Path(top.stdout.strip())
        allowed=(HERE.parents[1].relative_to(git_root).as_posix()+'/')
        proc=subprocess.run(['git','status','--porcelain=v1','--untracked-files=all'],cwd=git_root,text=True,capture_output=True,check=True)
        outside=[]
        for line in proc.stdout.splitlines():
            path=line[3:].strip().strip('"').replace('\\','/')
            if ' -> ' in path:path=path.split(' -> ',1)[1]
            if path and not path.startswith(allowed):outside.append(line)
        if outside:fail(errors,'modified/untracked files outside manuscript project: '+' | '.join(outside))
    except Exception as exc:warnings.append(f'git boundary check unavailable: {exc}')
    return finish(errors,warnings,len(rows))

def finish(errors,warnings,count):
    print(f'WP1 validation: rows={count}, errors={len(errors)}, warnings={len(warnings)}')
    for x in warnings:print('WARNING:',x)
    for x in errors:print('ERROR:',x)
    return 1 if errors else 0
if __name__=='__main__':sys.exit(main())

