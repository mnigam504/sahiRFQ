"""Compare buyer-entered quotes only after RFQ compatibility checks.

Tax and freight are explicit quoted amounts, not inferred tax rules. An
incomplete quote has a known subtotal but never a claimed delivered total.
"""
import math


def compare(engine, request_text, answers, quotes):
    result=engine.analyze(request_text,answers)
    if result['status']!='ready_for_supplier_confirmation':
        raise ValueError('Resolve the RFQ and obtain a compatible candidate before comparing quotes.')
    if not isinstance(quotes,list) or not 1<=len(quotes)<=10:
        raise ValueError('Provide between one and ten quotes.')
    eligible={h['record']['id']:h['record'] for h in result['candidates'] if h['eligibility']=='compatible'}
    quantity=result['rfq']['quantity']
    out=[]
    seen=set()
    for q in quotes:
        if not isinstance(q,dict) or q.get('record_id') not in eligible or q['record_id'] in seen:
            raise ValueError('Quote IDs must be distinct compatible catalog candidates.')
        seen.add(q['record_id'])
        r=eligible[q['record_id']]
        if q.get('price_unit')!=r['price_unit']:
            raise ValueError('Quote price unit does not match the RFQ quantity unit.')
        values={}
        for field in ['unit_price_inr','tax_total_inr','freight_total_inr']:
            value=q.get(field)
            if value is None or value=='':
                if field=='unit_price_inr': raise ValueError('A quoted unit price is required.')
                values[field]=None
            else:
                try: number=float(value)
                except (TypeError,ValueError): raise ValueError('Quote amounts must be nonnegative numbers.') from None
                if isinstance(value,bool) or not math.isfinite(number) or number<0 or number>10**9:
                    raise ValueError('Quote amounts must be finite nonnegative numbers.')
                values[field]=number
        base=round(values['unit_price_inr']*quantity,2)
        missing=[f for f in ['tax_total_inr','freight_total_inr'] if values[f] is None]
        subtotal=round(base+sum(v for f,v in values.items() if f!='unit_price_inr' and v is not None),2)
        out.append({'record_id':r['id'],'quantity':quantity,'price_unit':r['price_unit'],**values,
                    'goods_base_inr':base,'known_subtotal_inr':subtotal,
                    'quoted_total_inr':None if missing else subtotal,'missing_components':missing,
                    'provenance':'buyer_entered_quote','catalog_source':r['source']})
    complete=[q for q in out if q['quoted_total_inr'] is not None]
    all_complete=len(complete)==len(out)
    return {'quotes':out,'lowest_complete_quote':min(complete,key=lambda q:q['quoted_total_inr'])['record_id'] if all_complete else None,
            'comparison_status':'comparable' if all_complete else 'incomplete',
            'notice':'Quoted total = unit price x quantity + explicit total tax + explicit freight. No tax rule, supplier quality, or final fulfillment is inferred.'}
