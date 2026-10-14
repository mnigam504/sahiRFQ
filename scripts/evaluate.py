"""Reproducible development regression evaluation, with a raw TF-IDF baseline."""
import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import sklearn
from sahirfq.engine import Engine,normalize


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'reports'/'evaluation.json'))
    args=parser.parse_args()
    cases=json.loads((ROOT/'data'/'evaluation_cases.json').read_text())
    engine=Engine()
    train=json.loads((ROOT/'data'/'training.json').read_text())
    train_texts={normalize(r['text']) for r in train}
    assert not any(normalize(c['text']) in train_texts for c in cases),'Exact request overlap with training data.'
    scenarios=[]
    raw_category_correct=0
    supported=0
    returned=0
    violations=0
    baseline_returned=0
    baseline_violations=0
    safe_recalls=[]
    base_recalls=[]
    for c in cases:
        r=engine.analyze(c['text'],c.get('answers'))
        ids=[h['record']['id'] for h in r['shortlist']]
        errors=[]
        if r['status']!=c['expected_status']: errors.append('status')
        if r['rfq']['category']!=c['category']: errors.append('category_route')
        if set(ids)!=set(c.get('expected_shortlist',[])): errors.append('shortlist')
        for field,value in c.get('expected_fields',{}).items():
            actual=r['rfq']['specs'].get(field[6:]) if field.startswith('specs.') else r['rfq'].get(field)
            if actual!=value: errors.append('field:'+field)
        if not set(c.get('required_questions',[]))<={q['field'] for q in r['questions']}: errors.append('clarification_questions')
        if c.get('must_warn') and not r['warnings']: errors.append('manual_review')
        if c['category']:
            supported+=1
            raw_category_correct+=r['rfq']['routing']['predictions'][0]['category']==c['category']
        baseline=[]
        if c.get('fully_specified'):
            # Baseline deliberately uses only raw word TF-IDF, no router/constraints.
            query=engine.index.word.transform([normalize(c['text'])])
            scores=(engine.index.wmat@query.T).toarray().ravel()
            baseline=[engine.catalog[int(i)]['id'] for i in np.argsort(-scores,kind='stable')[:3]]
            allowed=set(c.get('compatible_ids',[]))
            returned+=len(ids)
            violations+=sum(i not in allowed for i in ids)
            baseline_returned+=len(baseline)
            baseline_violations+=sum(i not in allowed for i in baseline)
            if allowed:
                safe_recalls.append(len(set(ids)&allowed)/min(3,len(allowed)))
                base_recalls.append(len(set(baseline)&allowed)/min(3,len(allowed)))
        scenarios.append({'id':c['id'],'label':c['label'],'text':c['text'],'expected_status':c['expected_status'],
                          'observed_status':r['status'],'expected_shortlist':c.get('expected_shortlist',[]),
                          'observed_shortlist':ids,'baseline_top3':baseline,'passed':not errors,'failures':errors})
    # Warm inference distribution, startup and model fitting excluded.
    times=[]
    for c in cases:
        for _ in range(3):
            st=time.perf_counter();engine.analyze(c['text'],c.get('answers'));times.append((time.perf_counter()-st)*1000)
    summary={'total':len(cases),'passed':sum(s['passed'] for s in scenarios),
             'supported_category_cases':supported,'raw_category_accuracy_percent':round(100*raw_category_correct/supported,2),
             'fully_specified_cases':sum(bool(c.get('fully_specified')) for c in cases),
             'shortlist_records_checked':returned,'shortlist_violations':violations,
             'constraint_violation_rate_percent':round(100*violations/returned,2) if returned else None,
             'baseline_records_checked':baseline_returned,'baseline_violations':baseline_violations,
             'baseline_constraint_violation_rate_percent':round(100*baseline_violations/baseline_returned,2) if baseline_returned else None,
             'mean_compatible_recall_at3':round(float(np.mean(safe_recalls)),4) if safe_recalls else None,
             'baseline_mean_compatible_recall_at3':round(float(np.mean(base_recalls)),4) if base_recalls else None,
             'warm_latency_median_ms':round(float(np.median(times)),2),'warm_latency_p95_ms':round(float(np.percentile(times,95)),2),
             'latency_samples':len(times)}
    output={'summary':summary,'scenarios':scenarios,
            'method':{'dataset':'Separately authored fictional regression scenarios. Reviewed during development; not an untouched test set.',
                      'baseline':'Word TF-IDF top 3, without category routing or constraint checks. Not an IndiaMART benchmark.',
                      'constraint_truth':'Independent, authored compatible record ID sets in evaluation_cases.json.',
                      'recall':'Per nonempty compatible set, |top3 intersect compatible| / min(3, |compatible|); then mean.',
                      'timing':'Warm local matching, three repetitions per request; no network or LLM call; excludes training/startup.',
                      'llm':'Optional live provider performance is not measured. Provider responses are tested using mocks.'},
            'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'system':platform.system()},
            'fingerprints':{'catalog':engine.index.fingerprint,'evaluation':hashlib.sha256((ROOT/'data'/'evaluation_cases.json').read_bytes()).hexdigest()}}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    failures=[s for s in scenarios if not s['passed']]
    for f in failures: print('FAIL',f['id'],f['failures'],f['observed_status'],f['observed_shortlist'])
    if failures: sys.exit(1)

if __name__=='__main__': main()
