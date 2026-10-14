"""Inspect learned classifier features and a seed-family-separated sanity check."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from sklearn.metrics import classification_report,confusion_matrix
from sahirfq.ml import Router,load_json


def main():
    rows=load_json('training.json')
    train=[r for r in rows if r['seed_index']<6]
    validation=[r for r in rows if r['seed_index']>=6]
    assert {r['seed_id'] for r in train}.isdisjoint({r['seed_id'] for r in validation})
    router=Router(train)
    labels=router.model.classes_.tolist()
    actual=[r['category'] for r in validation]
    predicted=router.model.predict([r['text'] for r in validation]).tolist()
    report=classification_report(actual,predicted,output_dict=True,zero_division=0)
    all_router=Router(rows)
    features=all_router.model.named_steps['features'].get_feature_names_out()
    coefficients=all_router.model.named_steps['classifier'].coef_
    top={str(cat):[{'feature':str(features[int(i)]),'weight':round(float(coefficients[n,i]),4)}
                   for i in np.argsort(coefficients[n])[::-1][:12]]
         for n,cat in enumerate(all_router.model.classes_)}
    out={'grouped_validation':{'training_rows':len(train),'validation_rows':len(validation),
                              'split':'Seeds 0-5 per category train; seeds 6-7 per category validate. No shared seed family.',
                              'classification_report':report,'labels':labels,'confusion_matrix':confusion_matrix(actual,predicted,labels=labels).tolist(),
                              'limitation':'Synthetic sanity check only; templates and vocabulary are authored and do not represent real traffic.'},
         'shipped_model_training_rows':len(rows),'feature_count':len(features),'top_learned_features':top,
         'calibration':'None. Scores are not real-world calibrated confidence.'}
    (ROOT/'reports'/'model_inspection.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Grouped synthetic sanity-check accuracy:',round(report['accuracy'],3))
    print('Train/validation rows:',len(train),len(validation),'Feature count:',len(features))
    print('Wrote reports/model_inspection.json')

if __name__=='__main__': main()
