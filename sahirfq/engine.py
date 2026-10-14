"""Buyer extraction -> clarification -> retrieval -> three-valued constraint checks.

Unknown catalog fields never become confirmed matches. Missing buyer values
are never filled from the most popular supplier or the model's imagination.
"""
import math
import re
import time
from collections import Counter

from .ml import CatalogIndex, Router, load_json

CITIES = ['Agra','Delhi','Noida','Jaipur','Kanpur','Pune','Mumbai','Kolkata','Bengaluru','Chennai','Lucknow','Hathras','Kharagpur']
ANCHORS = {
    'water_pump': r'\b(pump|pumps|submersible|monoblock|borewell)\b',
    'packaging_box': r'\b(corrugated|carton|cartons|cardboard|boxes|box|dabbe)\b',
    'safety_glove': r'\b(gloves?|dastane)\b',
    'solar_panel': r'\b(solar|photovoltaic|pv)\b',
    'air_compressor': r'\b(compressors?|compressed air)\b',
}
SPECS = {
    'pump_type':['submersible','monoblock'], 'phase':['single','three'],
    'material':['nitrile','latex','cotton'], 'size':['S','M','L','XL'],
    'cell_type':['mono','poly'],
}
NUMERIC_SPECS = {'power_hp','ply','wattage','pressure_bar','tank_l'}


def normalize(text):
    text = text.lower().replace('×','x').replace('₹','rs ').replace(',', '')
    replacements = {'सोलर':'solar','बिजली':'electric','पैनल':'panel','पानी':'water','पंप':'pump',
                    'मोटर':'motor','पैकिंग':'packing','गत्ते':'cardboard','डिब्बे':'boxes',
                    'सुरक्षा':'safety','दस्ताने':'gloves','एयर':'air','कंप्रेसर':'compressor',
                    'नग':'pieces','जोड़े':'pairs','दिन':'days','अगरा':'agra', 'दिल्ली':'delhi',
                    'din':'days','bore well':'borewell','single-phase':'single phase',
                    'three-phase':'three phase','3 phase':'three phase','1 phase':'single phase',
                    'monocrystalline':'mono','polycrystalline':'poly','monocrytalline':'mono',
                    'submerssible':'submersible','corugated':'corrugated'}
    for old,new in replacements.items():
        text = re.sub(r'(?<!\w)'+re.escape(old)+r'(?!\w)', new, text)
    # Only expand numeric k suffixes; do not mutate category words.
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s*k\b',lambda m:str(float(m[1])*1000),text)
    return text


def unit_name(unit):
    return 'pairs' if unit.startswith(('pair','jodi')) else ('kg' if unit.startswith(('kg','kilo')) else 'pieces')


def clean_value(field, value, category, policies):
    if field == 'category':
        if value not in policies:
            raise ValueError('Choose a supported product category.')
        return value
    if field in {'quantity','lead_days'}:
        if isinstance(value,bool) or not str(value).strip().isdigit() or int(value)<=0 or int(value)>10**8:
            raise ValueError(f'{field} must be a positive whole number.')
        return int(value)
    if field in {'budget_amount'} | NUMERIC_SPECS:
        try:
            number = float(value)
        except (TypeError,ValueError):
            raise ValueError(f'{field} must be a positive number.') from None
        if isinstance(value,bool) or not math.isfinite(number) or number<=0 or number>10**9:
            raise ValueError(f'{field} must be a positive number.')
        if field in {'ply','wattage','tank_l'} and number != int(number):
            raise ValueError(f'{field} must be a whole number.')
        return int(number) if number.is_integer() else number
    if field == 'quantity_unit':
        if value not in ['pieces','pairs','kg']:
            raise ValueError('Supported quantity units: pieces, pairs, kg.')
        return value
    if field == 'budget_scope':
        if value not in ['per_unit','total']:
            raise ValueError('Budget scope must be per_unit or total.')
        return value
    if field == 'delivery_city':
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z .-]{1,59}',value):
            raise ValueError('Use a city name in English letters.')
        return value.strip().title()
    if field in SPECS:
        canon = str(value).upper() if field=='size' else str(value).lower()
        if canon not in SPECS[field]:
            raise ValueError(f'{field}: choose from {", ".join(SPECS[field])}.')
        return canon
    if field=='dimensions_mm':
        canon = str(value).lower().replace(' ','').replace('×','x')
        if not re.fullmatch(r'\d+x\d+x\d+',canon) or any(int(n)<=0 for n in canon.split('x')):
            raise ValueError('Dimensions must be three positive mm values, e.g. 300x200x150.')
        return canon
    if field=='sterile':
        if value not in (True,False,'true','false'):
            raise ValueError('sterile must be true or false.')
        return value in (True,'true')
    raise ValueError(f'Unsupported clarification field: {field}')


class Engine:
    def __init__(self):
        self.policies = load_json('policies.json')
        self.catalog = load_json('catalog.json')
        self.router = Router()
        self.index = CatalogIndex(self.catalog)

    def extract(self, raw, answers=None):
        if not isinstance(raw,str) or not 1<=len(raw.strip())<=4000:
            raise ValueError('Enter a buyer request between 1 and 4,000 characters.')
        answers = answers or {}
        if not isinstance(answers,dict):
            raise ValueError('answers must be an object.')
        t = normalize(raw)
        predictions = self.router.predict(t)
        coverage = [cat for cat,pattern in ANCHORS.items() if re.search(pattern,t)]
        category = predictions[0]['category']
        routing_reason = None
        if len(coverage)!=1 or category not in coverage:
            routing_reason = 'unsupported_or_multiple_categories'
            category = None
        elif predictions[0]['probability']<.45 or predictions[0]['probability']-predictions[1]['probability']<.15:
            routing_reason = 'weak_model_evidence'
            category = None
        if re.search(r'\b(fuel|vacuum|hydraulic|breast|heat)\s+pump\b',t):
            category = None
            routing_reason = 'unsupported_pump_type'
        rfq = {'raw_text':raw,'category':category,'quantity':None,'quantity_unit':None,
               'delivery_city':None,'lead_days':None,'budget_amount':None,'budget_scope':None,
               'local_only':bool(re.search(r'\b(local only|only local|same city only)\b',t)),
               'specs':{},'evidence':{},'warnings':[], 'routing':{'predictions':predictions,'reason':routing_reason}}

        def put(field, pairs, spec=False):
            # Pair = extracted value, literal span from normalized buyer text.
            values = {str(p[0]):p for p in pairs}
            if len(values)>1:
                rfq['warnings'].append({'field':field,'message':f'Conflicting or multiple {field} values. Please choose one.'})
            elif len(values)==1:
                value, span = next(iter(values.values()))
                (rfq['specs'] if spec else rfq)[field]=value
                rfq['evidence'][field]={'value':value,'source':'buyer_text','normalized_span':span}

        quantities = list(re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)\s*(pieces?|pcs|units?|boxes?|cartons?|panels?|pumps?|pairs?|jodi|kg|kilograms?)\b',t))
        put('quantity',[(int(float(m[1])) if float(m[1]).is_integer() else float(m[1]),m[0]) for m in quantities])
        put('quantity_unit',[(unit_name(m[2]),m[0]) for m in quantities])
        put('delivery_city',[(city,city.lower()) for city in CITIES if re.search(r'\b'+city.lower()+r'\b',t)])
        put('lead_days',[(int(m[1]),m[0]) for m in re.finditer(r'(?<![\w.])(?:within|in|by|andar)?\s*(-?\d+)\s*days?\b',t)])
        bm = list(re.finditer(r'\b(?:budget(?: of)?|under|below|upto|up to|max(?:imum)?|rs|inr)\s*(?:rs|inr)?\s*(-?\d+(?:\.\d+)?)\s*(lakh|lakhs|thousand)?',t))
        put('budget_amount',[(float(m[1])*(100000 if m[2] in ['lakh','lakhs'] else 1000 if m[2]=='thousand' else 1),m[0]) for m in bm])
        scopes=[]
        if re.search(r'\b(per|each)\b|/(?:piece|pair|box|unit)',t): scopes.append(('per_unit','per/each'))
        if re.search(r'\b(total|overall)\b',t): scopes.append(('total','total/overall'))
        put('budget_scope',scopes)
        if rfq['budget_amount'] is not None and rfq['budget_scope'] is None:
            rfq['warnings'].append({'field':'budget_scope','message':'Budget found, but per-unit versus total scope is unclear.'})

        if category=='water_pump':
            put('pump_type',[(s,s) for s in SPECS['pump_type'] if re.search(r'\b'+s+r'\b',t)],True)
            put('power_hp',[(float(m[1]),m[0]) for m in re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)\s*hp\b',t)],True)
            put('phase',[(s,s+' phase') for s in SPECS['phase'] if re.search(r'\b'+s+r'\s+phase\b',t)],True)
        elif category=='packaging_box':
            dims=[]
            for m in re.finditer(r'\b(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(mm|cm)\b',t):
                vals=[float(m[i])*(10 if m[4]=='cm' else 1) for i in [1,2,3]]
                if all(v.is_integer() for v in vals): dims.append(('x'.join(str(int(v)) for v in vals),m[0]))
            put('dimensions_mm',dims,True)
            put('ply',[(int(m[1]),m[0]) for m in re.finditer(r'\b(\d+)\s*[- ]?ply\b',t)],True)
        elif category=='safety_glove':
            put('material',[(s,s) for s in SPECS['material'] if re.search(r'\b'+s+r'\b',t)],True)
            sizes={'small':'S','medium':'M','large':'L','extra large':'XL'}
            # XL is handled before L; overlapping language is not double counted.
            masked=t.replace('extra large','size xl')
            pairs=[(v,k) for k,v in sizes.items() if k!='extra large' and re.search(r'\b'+k+r'\b',masked)]
            pairs += [(m[1].upper(),m[0]) for m in re.finditer(r'\bsize\s*(xl|s|m|l)\b',masked)]
            put('size',pairs,True)
            if re.search(r'\bnon[- ]?sterile\b',t): put('sterile',[(False,'non sterile')],True)
            elif re.search(r'\bsterile\b',t): put('sterile',[(True,'sterile')],True)
        elif category=='solar_panel':
            put('wattage',[(int(m[1]),m[0]) for m in re.finditer(r'\b(\d+)\s*(?:w|watt|watts)\b',t)],True)
            put('cell_type',[(s,s) for s in SPECS['cell_type'] if re.search(r'\b'+s+r'\b',t)],True)
        elif category=='air_compressor':
            put('pressure_bar',[(float(m[1]),m[0]) for m in re.finditer(r'\b(\d+(?:\.\d+)?)\s*bar\b',t)],True)
            put('tank_l',[(int(m[1]),m[0]) for m in re.finditer(r'\b(\d+)\s*(?:litre|liter|litres|liters|l)\b',t)],True)
        if re.search(r'\b(not|except|excluding|nahi|avoid|instead|or)\b',t):
            rfq['warnings'].append({'field':'request_review','message':'Alternatives or exclusions need manual review; this parser cannot safely resolve them.'})
        qualifiers=re.findall(r'\b(?:certified|certification|isi|bis|warranty|bifacial|stainless steel|food[- ]grade|food safe|medical|surgical|psi|voltage|volts|flow|head|diameter|temperature|centrifugal|suction)\b',t)
        if category!='air_compressor' and re.search(r'\b(?:pressure|bar|litre tank)\b',t):
            qualifiers.append('pressure/capacity requirement outside modeled category fields')
        if qualifiers:
            rfq['warnings'].append({'field':'request_review','message':'Unmodeled requirement(s): '+', '.join(sorted(set(qualifiers)))+'. Keep these in the RFQ and verify manually.'})
        # The category correction must happen first, independent of JSON key order.
        if answers.get('category') not in (None,''):
            cat=clean_value('category',answers['category'],category,self.policies)
            if cat!=category:
                rfq['specs']={}
                rfq['evidence']={k:v for k,v in rfq['evidence'].items() if k not in NUMERIC_SPECS|set(SPECS)|{'dimensions_mm','sterile'}}
            rfq['category']=cat
            rfq['routing']['reason']='buyer_selected_category'
            rfq['evidence']['category']={'value':cat,'source':'buyer_clarification'}
        for field,value in answers.items():
            if field=='category' or value is None or value=='': continue
            cat=rfq['category']
            is_spec=field in NUMERIC_SPECS or field in SPECS or field in {'dimensions_mm','sterile'}
            if is_spec and (cat is None or field not in self.policies[cat]['critical']+(['sterile'] if cat=='safety_glove' else [])):
                raise ValueError(f'{field} is not applicable to the selected category.')
            value=clean_value(field,value,cat,self.policies)
            (rfq['specs'] if is_spec else rfq)[field]=value
            rfq['evidence'][field]={'value':value,'source':'buyer_clarification'}
            rfq['warnings']=[w for w in rfq['warnings'] if w['field']!=field]
        for f in ['quantity','lead_days','budget_amount']:
            value=rfq[f]
            if value is not None and (value<=0 or (f!='budget_amount' and value!=int(value))):
                rfq['warnings'].append({'field':f,'message':f'{f} must be positive'+(' and a whole number.' if f!='budget_amount' else '.')})
                rfq[f]=None
        for field,value in list(rfq['specs'].items()):
            try: clean_value(field,value,rfq['category'],self.policies)
            except ValueError:
                del rfq['specs'][field]
                rfq['warnings'].append({'field':field,'message':f'Invalid {field}; clarify it.'})
        return rfq

    def check(self, r, rfq):
        checks=[]
        def add(field, required, actual, passed, source_field=None):
            checks.append({'field':field,'required':required,'catalog_value':actual,
                           'status':'unknown' if actual is None else ('pass' if passed else 'fail'),
                           'citation':f"{r['source']}.{source_field or field}"})
        add('category',rfq['category'],r['category'],r['category']==rfq['category'])
        for key,wanted in rfq['specs'].items():
            actual=r['specs'].get(key)
            add('specs.'+key,wanted,actual,actual==wanted)
        qty=rfq['quantity']
        if rfq['quantity_unit'] is not None:
            add('price_unit',rfq['quantity_unit'],r['price_unit'],rfq['quantity_unit']==r['price_unit'])
        if qty is not None: add('moq',f'<= {qty}',r['moq'],r['moq'] is not None and r['moq']<=qty)
        if rfq['lead_days'] is not None:
            add('lead_days',f"<= {rfq['lead_days']}",r['lead_days'],r['lead_days'] is not None and r['lead_days']<=rfq['lead_days'])
        if rfq['budget_amount'] is not None and rfq['budget_scope'] is not None:
            cost = r['unit_price_inr'] if rfq['budget_scope']=='per_unit' else (r['unit_price_inr']*qty if qty else None)
            add('base_cost_inr',f"<= {rfq['budget_amount']} ({rfq['budget_scope']}, ex tax/freight)",cost,cost is not None and cost<=rfq['budget_amount'],'unit_price_inr')
            checks[-1]['derivation']='Catalog unit_price_inr' + (' x buyer quantity' if rfq['budget_scope']=='total' else '')
        if rfq['delivery_city']:
            add('ships_to',rfq['delivery_city'],r['ships_to'],r['ships_to'] is not None and ('all_india' in r['ships_to'] or rfq['delivery_city'] in r['ships_to']))
        if rfq['local_only'] and rfq['delivery_city']:
            add('dispatch_city',rfq['delivery_city'],r['dispatch_city'],r['dispatch_city']==rfq['delivery_city'])
        return checks

    def questions(self,rfq,candidates):
        cat=rfq['category']
        missing=['category'] if not cat else [f for f in self.policies[cat]['critical'] if rfq['specs'].get(f) is None]
        missing += [f for f in ['quantity','quantity_unit','delivery_city'] if rfq[f] is None]
        if rfq['budget_amount'] is not None and rfq['budget_scope'] is None: missing.append('budget_scope')
        labels={'category':'Which product category do you need?','quantity':'How many units do you need?',
                'quantity_unit':'Is the quantity in pieces or pairs?','delivery_city':'Which city should receive the order?',
                'budget_scope':'Is that budget per unit or for the entire order?'}
        qs=[]
        for f in dict.fromkeys(missing):
            values=[r['specs'].get(f) for r in candidates if r['specs'].get(f) is not None]
            counts=Counter(str(v) for v in values)
            n=len(values)
            entropy=-sum((v/n)*math.log2(v/n) for v in counts.values()) if n else 0.0
            options=sorted(set(values),key=str)
            if f=='category': options=list(self.policies)
            elif f=='quantity_unit': options=['pieces','pairs']
            elif f=='budget_scope': options=['per_unit','total']
            label=labels.get(f,'Please specify '+self.policies[cat]['fields'].get(f,f)+'.') if cat else labels.get(f,f)
            qs.append({'field':f,'question':label,'options':options,'catalog_partition_bits':round(entropy,3),
                       'priority':round(2+entropy+(3 if f=='category' else 0),3),
                       'basis':'Missing quote-critical buyer field; entropy measures catalog diversity, not business uplift.'})
        return sorted(qs,key=lambda q:(-q['priority'],q['field']))

    def analyze(self, text, answers=None):
        start=time.perf_counter()
        rfq=self.extract(text,answers)
        cat=rfq['category']
        retrieved=self.index.search(normalize(text))
        trace=[{'step':'classify','detail':f"Supervised router trained on {self.router.training_count} template-derived examples; coverage gate applied."}]
        checked=[]
        for hit in retrieved:
            if not cat or hit['record']['category']!=cat: continue
            checks=self.check(hit['record'],rfq)
            failed=[c for c in checks if c['status']=='fail']
            unknown=[c for c in checks if c['status']=='unknown']
            checked.append({**hit,'checks':checks,'eligibility':'excluded' if failed else ('unverified' if unknown else 'compatible'),
                            'failed_fields':[c['field'] for c in failed],'unknown_fields':[c['field'] for c in unknown]})
        viable=[h['record'] for h in checked if h['eligibility']!='excluded']
        qs=self.questions(rfq,viable)
        warnings=rfq['warnings'][:]
        if cat and rfq['quantity_unit'] and rfq['quantity_unit']!=self.policies[cat]['unit']:
            warnings.append({'field':'quantity_unit','message':f"This demo catalog prices {self.policies[cat]['label']} in {self.policies[cat]['unit']}; automatic unit conversion is not supported."})
        missing=bool(qs or warnings)
        compatible=[h for h in checked if h['eligibility']=='compatible']
        shortlist=[] if missing else compatible[:3]
        status='clarification_needed' if missing else ('ready_for_supplier_confirmation' if shortlist else 'no_confirmed_match')
        for hit in checked:
            hit['order_base_inr']=None if not rfq['quantity'] or rfq['quantity_unit']!=hit['record']['price_unit'] else rfq['quantity']*hit['record']['unit_price_inr']
        trace += [{'step':'extract','detail':f"{len(rfq['evidence'])} buyer-provided fields; unspecified values remain null."},
                  {'step':'retrieve','detail':f"Hybrid word/character/LSA retrieval across {len(self.catalog)} fictional catalog records."},
                  {'step':'verify','detail':f"{len(checked)} category candidates checked; {sum(h['eligibility']=='excluded' for h in checked)} excluded by explicit constraints."},
                  {'step':'decide','detail':f"{len(qs)} missing-field questions. Decision: {status}."}]
        return {'status':status,'rfq':rfq,'questions':qs,'warnings':warnings,'shortlist':shortlist,
                'candidates':checked,'trace':trace,'catalog_fingerprint':self.index.fingerprint,
                'latency_ms':round((time.perf_counter()-start)*1000,2),'llm_calls':0,
                'notice':'Fictional catalog. Compatibility is based on declared fields; supplier confirmation is required. Prices exclude tax and freight.'}

    def export_rfq(self,result):
        rfq=result['rfq']
        lines=['REQUEST FOR QUOTATION - BUYER REVIEW REQUIRED','',f"Original request: {rfq['raw_text']}",
               f"Category: {self.policies.get(rfq['category'],{}).get('label','TO CONFIRM')}"]
        for field in ['quantity','quantity_unit','delivery_city','lead_days','budget_amount','budget_scope']:
            lines.append(f"{field.replace('_',' ').title()}: {rfq[field] if rfq[field] is not None else 'TO CONFIRM'}")
        lines.extend(f"{k}: {v}" for k,v in rfq['specs'].items())
        if result['questions']: lines += ['','Open questions:']+[q['question'] for q in result['questions']]
        if result['warnings']: lines += ['','Manual review:']+[w['message'] for w in result['warnings']]
        lines += ['','Please quote: matching specification, MOQ, base price and price unit, taxes, freight,',
                  'delivery date, payment terms, and validity. Confirm all missing catalog fields.',
                  'This is a draft. No supplier has been contacted and no order has been placed.']
        return '\n'.join(lines)
