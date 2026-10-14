"""Rebuild the explicitly fictional catalog and template-derived ML training data.

No marketplace pages, personal data, or real supplier claims are copied.
Evaluation requests live in a separate hand-authored file.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(name, obj):
    (ROOT / 'data' / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    policies = {
        'water_pump': {'label': 'Water pumps', 'unit': 'pieces', 'critical': ['pump_type', 'power_hp', 'phase'],
                       'fields': {'pump_type': 'Pump type', 'power_hp': 'Power in HP', 'phase': 'Electrical phase'}},
        'packaging_box': {'label': 'Corrugated boxes', 'unit': 'pieces', 'critical': ['dimensions_mm', 'ply'],
                          'fields': {'dimensions_mm': 'Dimensions in mm (L x W x H)', 'ply': 'Number of plies'}},
        'safety_glove': {'label': 'Safety gloves', 'unit': 'pairs', 'critical': ['material', 'size'],
                         'fields': {'material': 'Glove material', 'size': 'Glove size'}},
        'solar_panel': {'label': 'Solar panels', 'unit': 'pieces', 'critical': ['wattage', 'cell_type'],
                        'fields': {'wattage': 'Rated wattage', 'cell_type': 'Cell type'}},
        'air_compressor': {'label': 'Air compressors', 'unit': 'pieces', 'critical': ['pressure_bar', 'tank_l'],
                           'fields': {'pressure_bar': 'Required pressure in bar', 'tank_l': 'Tank capacity in litres'}}
    }
    write('policies.json', policies)
    # id, category, title, city, price, MOQ, days, specs
    rows = [
        ('P01','water_pump','2 HP single phase submersible pump','Agra',9800,1,4,{'pump_type':'submersible','power_hp':2,'phase':'single'}),
        ('P02','water_pump','2 HP three phase submersible pump','Noida',9200,2,5,{'pump_type':'submersible','power_hp':2,'phase':'three'}),
        ('P03','water_pump','1 HP single phase monoblock pump','Agra',4800,1,2,{'pump_type':'monoblock','power_hp':1,'phase':'single'}),
        ('P04','water_pump','2 HP single phase monoblock pump','Jaipur',8400,1,6,{'pump_type':'monoblock','power_hp':2,'phase':'single'}),
        ('P05','water_pump','2 HP single phase submersible pump - bulk','Kanpur',8700,10,9,{'pump_type':'submersible','power_hp':2,'phase':'single'}),
        ('P06','water_pump','2 HP submersible pump - phase unspecified','Delhi',8000,1,3,{'pump_type':'submersible','power_hp':2,'phase':None}),
        ('B01','packaging_box','5 ply corrugated box 300 x 200 x 150 mm','Delhi',28,500,5,{'dimensions_mm':'300x200x150','ply':5}),
        ('B02','packaging_box','3 ply corrugated carton 300 x 200 x 150 mm','Agra',19,100,3,{'dimensions_mm':'300x200x150','ply':3}),
        ('B03','packaging_box','5 ply corrugated box 400 x 300 x 200 mm','Noida',43,500,6,{'dimensions_mm':'400x300x200','ply':5}),
        ('B04','packaging_box','5 ply corrugated box 300 x 200 x 150 mm - small batches','Pune',33,100,4,{'dimensions_mm':'300x200x150','ply':5}),
        ('B05','packaging_box','5 ply corrugated box 300 x 200 x 150 mm - bulk','Jaipur',24,2000,10,{'dimensions_mm':'300x200x150','ply':5}),
        ('B06','packaging_box','5 ply custom corrugated box - size pending','Delhi',23,100,4,{'dimensions_mm':None,'ply':5}),
        ('G01','safety_glove','Large nitrile industrial safety gloves','Delhi',45,50,3,{'material':'nitrile','size':'L','sterile':False}),
        ('G02','safety_glove','Medium latex safety gloves','Agra',32,100,4,{'material':'latex','size':'M','sterile':False}),
        ('G03','safety_glove','Large cotton industrial gloves','Jaipur',18,100,5,{'material':'cotton','size':'L','sterile':False}),
        ('G04','safety_glove','Medium nitrile industrial gloves','Noida',44,50,2,{'material':'nitrile','size':'M','sterile':False}),
        ('G05','safety_glove','Large nitrile industrial gloves - bulk','Pune',39,1000,8,{'material':'nitrile','size':'L','sterile':False}),
        ('G06','safety_glove','Large nitrile gloves - sterility unspecified','Delhi',42,50,3,{'material':'nitrile','size':'L','sterile':None}),
        ('S01','solar_panel','550 W monocrystalline solar panel','Noida',12000,2,7,{'wattage':550,'cell_type':'mono'}),
        ('S02','solar_panel','330 W polycrystalline solar panel','Delhi',6800,5,5,{'wattage':330,'cell_type':'poly'}),
        ('S03','solar_panel','450 W monocrystalline solar panel','Jaipur',9900,2,6,{'wattage':450,'cell_type':'mono'}),
        ('S04','solar_panel','550 W monocrystalline panel - large orders','Pune',11300,20,12,{'wattage':550,'cell_type':'mono'}),
        ('S05','solar_panel','550 W polycrystalline solar panel','Kanpur',10800,5,8,{'wattage':550,'cell_type':'poly'}),
        ('S06','solar_panel','550 W solar module - technology unspecified','Delhi',10500,2,5,{'wattage':550,'cell_type':None}),
        ('C01','air_compressor','8 bar 100 litre air compressor','Delhi',28000,1,5,{'pressure_bar':8,'tank_l':100}),
        ('C02','air_compressor','8 bar 50 litre air compressor','Agra',17000,1,3,{'pressure_bar':8,'tank_l':50}),
        ('C03','air_compressor','10 bar 100 litre air compressor','Noida',33000,1,7,{'pressure_bar':10,'tank_l':100}),
        ('C04','air_compressor','8 bar 100 litre air compressor - bulk','Jaipur',25500,5,10,{'pressure_bar':8,'tank_l':100}),
        ('C05','air_compressor','8 bar 200 litre air compressor','Pune',44000,1,8,{'pressure_bar':8,'tank_l':200}),
        ('C06','air_compressor','100 litre air compressor - pressure pending','Delhi',24500,1,4,{'pressure_bar':None,'tank_l':100}),
    ]
    records=[]
    for rid, cat, title, city, price, moq, days, specs in rows:
        records.append({'id':rid,'category':cat,'title':title,'supplier':f'Demo Supplier {rid}',
                        'dispatch_city':city,'ships_to':['all_india'],'unit_price_inr':price,
                        'price_unit':policies[cat]['unit'],'price_scope':'ex_tax_ex_freight',
                        'moq':moq,'lead_days':days,'specs':specs,
                        'source':f'data/catalog.json#{rid}','provenance':'fictional_demo',
                        'verified_on':None})
    write('catalog.json', records)
    seeds={
      'water_pump':['submersible water pump','monoblock water pump','borewell motor pump','single phase irrigation pump',
                    'three phase water pumping motor','paani ki pump motor','पानी की पंप मोटर','agricultural submersible pump'],
      'packaging_box':['corrugated packaging boxes','cardboard shipping cartons','5 ply carton box','3 ply corrugated boxes',
                       'packing dabbe carton','corrugated carton for dispatch','पैकिंग के गत्ते के डिब्बे','custom corrugated boxes'],
      'safety_glove':['nitrile safety gloves','latex protective gloves','cotton hand gloves','industrial safety gloves',
                      'haath ke dastane safety gloves','chemical protection nitrile gloves','सुरक्षा दस्ताने','large size latex gloves'],
      'solar_panel':['monocrystalline solar panels','polycrystalline photovoltaic modules','rooftop solar module','550 watt solar panel',
                     'solar bijli panel','सोलर बिजली पैनल','mono PV panels','poly solar plates'],
      'air_compressor':['industrial air compressor','compressed air tank machine','pneumatic air compressor','8 bar compressor machine',
                        'hawa compressor machine','एयर कंप्रेसर मशीन','100 litre air compression unit','workshop air compressor']}
    templates=['Need {} for my workshop','Quote bulk {} delivery to Delhi','{} chahiye Agra mein',
               'Please supply {} for our business','{} ka rate aur MOQ batao']
    train=[{'text':template.format(seed),'category':cat,'origin':'authored_seed_template',
            'seed_id':cat+'_'+str(i),'seed_index':i}
           for cat, examples in seeds.items() for i,seed in enumerate(examples) for template in templates]
    write('training.json',train)
    write('data_manifest.json',{'catalog_records':len(records),'training_records':len(train),'categories':len(policies),
                              'origin':'Authored fictional catalog and seed/template training requests. No IndiaMART internal data.',
                              'license':'MIT','evaluation_origin':'Separately authored scenario fixtures; not representative customer traffic.',
                              'split':'Training seeds/templates only; scenario evaluation is never fitted.',
                              'generated_on':'2026-10-14'})
    print(f'Wrote {len(records)} catalog records and {len(train)} template-derived training records.')

if __name__=='__main__':
    main()
