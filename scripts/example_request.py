"""A minimal script for inspecting the pipeline without the web UI."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sahirfq.engine import Engine

engine=Engine()
text='Agra ke liye 3 pieces pump chahiye within 7 days. Budget Rs 10000 per unit.'
initial=engine.analyze(text)
print('INITIAL:',initial['status'])
for q in initial['questions']: print(q['field'],q['question'],q['options'])
clarified=engine.analyze(text,{'pump_type':'submersible','power_hp':2,'phase':'single'})
print('\nAFTER BUYER ANSWERS:',clarified['status'])
print('Shortlist:',[h['record']['id'] for h in clarified['shortlist']])
print('\nAll candidate decisions:')
for h in clarified['candidates']:
    print(h['record']['id'],h['eligibility'],'failed:',h['failed_fields'],'unknown:',h['unknown_fields'])
print('\nRFQ DRAFT:\n'+engine.export_rfq(clarified))
