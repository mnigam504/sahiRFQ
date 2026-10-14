'use strict';
const $=id=>document.getElementById(id);
const presets=[
  ['Vague pump','Agra ke liye 3 pieces pump chahiye within 7 days. Budget Rs 10000 per unit.'],
  ['Complete pump','Agra ke liye 3 pieces 2 HP single phase submersible pump chahiye under Rs 10000 per unit within 7 days.'],
  ['Box dimensions','1000 boxes 5 ply corrugated 30 x 20 x 15 cm delivery Delhi under Rs 30 per box within 7 days.'],
  ['MOQ mismatch','Need 1 piece 2 HP three phase submersible water pump delivered to Noida within 6 days.'],
  ['Safety gloves','Need 100 pairs large nitrile industrial gloves delivery Delhi within 4 days.'],
  ['Unknown product','Need 500 kg aluminium ingots delivered to Pune.']
];
let current=null, answers={}, policies={};
function el(tag,className,text){const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=text;return n;}
function money(n){return n===null||n===undefined?'Unknown':'₹'+Number(n).toLocaleString('en-IN',{maximumFractionDigits:2});}
async function api(path,obj){const r=await fetch(path,obj===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Request failed.');return j;}
function metric(parent,value,label,note){const d=el('div','metric');d.append(el('span','',label),el('strong','',value),el('small','',note));parent.append(d);}
async function analyze(){
  $('analyze').disabled=true;$('clarify').disabled=true;$('error').textContent='';
  try{current=await api('/api/analyze',{text:$('request').value,answers});render();}
  catch(e){$('error').textContent=e.message;}
  finally{$('analyze').disabled=false;$('clarify').disabled=false;}
}
function render(){
  const r=current;
  for(const id of ['ask','download','compare-quotes'])$(id).disabled=false;
  const ready=r.status==='ready_for_supplier_confirmation';
  const decision=$('decision-title').closest('.decision');decision.classList.toggle('ready',ready);decision.classList.toggle('no-match',r.status==='no_confirmed_match');
  $('decision-title').textContent=ready?'A clear requirement. A defensible shortlist.':r.status==='no_confirmed_match'?'No confirmed catalog match.':'A few details will change the match.';
  $('decision-copy').textContent=ready?'These candidates match the declared fields. Confirm price, availability, tax and freight with the supplier.':r.status==='no_confirmed_match'?'Keep the buyer’s constraints. Request a supplier confirmation or broaden the requirement deliberately.':'Complete the missing buyer fields before treating any supplier as a recommendation.';
  $('decision-icon').textContent=ready?'✓':r.status==='no_confirmed_match'?'!':'?';
  $('metrics').replaceChildren();metric($('metrics'),r.shortlist.length,'SHORTLISTED','All declared constraints checked');metric($('metrics'),r.questions.length,'OPEN QUESTIONS','Buyer input still required');metric($('metrics'),r.latency_ms+' ms','LOCAL INFERENCE','No LLM call in matching');
  $('questions').replaceChildren();$('question-count').textContent=r.questions.length+' missing fields';
  $('clarify-panel').classList.toggle('hidden',!r.questions.length);
  for(const q of r.questions){
    const wrap=el('div');const label=el('label','',q.question);label.htmlFor='field-'+q.field;wrap.append(label);
    let input;
    if(q.options.length){input=el('select');const blank=el('option','','Choose…');blank.value='';input.append(blank);for(const v of q.options){const o=el('option','',q.field==='category'?policies[v].label:String(v).replaceAll('_',' '));o.value=v;input.append(o);}}
    else{input=el('input');input.placeholder=q.field==='delivery_city'?'e.g. Agra':q.field==='dimensions_mm'?'300x200x150':'Enter value';if(['quantity','power_hp','ply','wattage','pressure_bar','tank_l'].includes(q.field)){input.type='number';input.min='1';input.step=q.field==='power_hp'||q.field==='pressure_bar'?'any':'1';}}
    input.id='field-'+q.field;input.dataset.field=q.field;if(answers[q.field]!==undefined)input.value=answers[q.field];wrap.append(input,el('small','',q.catalog_partition_bits+' bits of catalog diversity'));$('questions').append(wrap);
  }
  $('warning-panel').classList.toggle('hidden',!r.warnings.length);$('warnings').replaceChildren(...r.warnings.map(w=>el('li','',w.message)));
  $('candidate-count').textContent=r.candidates.length+' category candidates';$('match-copy').textContent=ready?'Shortlisted candidates appear first. Every exclusion and unknown has a catalog citation.':'Exploratory candidates only. No recommendation is made while the RFQ is incomplete.';
  $('candidates').replaceChildren();
  const chosen=new Set(r.shortlist.map(h=>h.record.id));
  const order=[...r.candidates].sort((a,b)=>(chosen.has(b.record.id)-chosen.has(a.record.id))||(['compatible','unverified','excluded'].indexOf(a.eligibility)-['compatible','unverified','excluded'].indexOf(b.eligibility)));
  for(const h of order){
    const p=h.record,card=el('article','catalog-card '+h.eligibility),top=el('div','catalog-top'),name=el('div');
    name.append(el('p','record-title',p.title),el('p','supplier',p.id+' · '+p.supplier+' · '+p.dispatch_city));
    const status=chosen.has(p.id)?'Shortlisted':h.eligibility==='compatible'?(ready?'Compatible':'Exploratory'):h.eligibility==='unverified'?'Needs confirmation':'Excluded';
    top.append(name,el('span','tag '+h.eligibility,status));card.append(top);
    const specs=el('div','spec-line');specs.append(el('span','','MOQ '+p.moq+' '+p.price_unit),el('span','',p.lead_days+' days lead time'),el('span','','Retrieval score '+h.score.toFixed(2)));card.append(specs);
    const cost=el('div','cost-line'),base=el('div');base.append(el('strong','',money(p.unit_price_inr)),el('small','',' / '+p.price_unit.replace(/s$/,'')));cost.append(base,el('small','',h.order_base_inr===null?'Quantity basis pending':money(h.order_base_inr)+' goods base'));card.append(cost);
    const d=el('details'),s=el('summary','','Inspect '+h.checks.length+' field checks');d.append(s);
    for(const c of h.checks){const line=el('div','evidence-row');line.append(el('span',c.status,c.status.toUpperCase()),el('span','',c.field+': buyer '+String(c.required)+' · catalog '+(c.catalog_value===null?'UNKNOWN':String(c.catalog_value))));d.append(line,el('div','source',c.citation));}
    d.append(el('div','source','Retrieval signals: '+JSON.stringify(h.signals)));card.append(d);$('candidates').append(card);
  }
  if(!order.length)$('candidates').append(el('p','no-candidates','The request cannot be safely routed within this five-category catalog. Select the intended category or use manual sourcing.'));
  $('draft').textContent=r.rfq_draft;$('trace').replaceChildren(...r.trace.map(t=>el('li','',t.step+': '+t.detail)));
  $('answer').classList.add('hidden');$('citations').replaceChildren();
  $('quote-panel').classList.toggle('hidden',!ready);$('quote-inputs').replaceChildren();$('quote-result').replaceChildren();
  for(const h of r.shortlist){const row=el('div','quote-row');row.dataset.id=h.record.id;row.dataset.unit=h.record.price_unit;row.append(el('strong','',h.record.id+' · '+h.record.supplier));const grid=el('div','quote-fields');for(const [field,label,value] of [['unit_price_inr','Unit price (INR)',h.record.unit_price_inr],['tax_total_inr','Total quoted tax (INR)',''],['freight_total_inr','Total freight (INR)','']]){const w=el('div'),l=el('label','',label),i=el('input');i.type='number';i.min='0';i.step='any';i.value=value;i.placeholder='Unknown';i.dataset.field=field;i.id='quote-'+h.record.id+'-'+field;l.htmlFor=i.id;w.append(l,i);grid.append(w);}row.append(grid);$('quote-inputs').append(row);}
}
for(const [label,text]of presets){const b=el('button','preset',label);b.addEventListener('click',()=>{$('request').value=text;answers={};analyze();});$('presets').append(b);}
$('request').addEventListener('input',()=>{answers={};current=null;for(const id of ['ask','download','compare-quotes'])$(id).disabled=true;$('decision-title').textContent='Request changed. Analyze to refresh.';$('decision-copy').textContent='The results below belong to the previous analyzed request.';});
$('analyze').addEventListener('click',analyze);
$('clarify').addEventListener('click',()=>{for(const i of $('questions').querySelectorAll('[data-field]'))if(i.value!=='')answers[i.dataset.field]=i.value;analyze();});
$('download').addEventListener('click',()=>{if(!current)return;const blob=new Blob([current.rfq_draft],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),a=el('a');a.href=url;a.download='SahiRFQ_buyer_review_draft.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('ask').addEventListener('click',async()=>{if(!current)return;$('ask').disabled=true;$('answer').classList.remove('hidden');$('answer').textContent='Retrieving catalog evidence…';$('citations').replaceChildren();try{const ids=current.shortlist.map(h=>h.record.id);const j=await api('/api/ask',{question:$('question').value,record_ids:ids.length?ids:undefined,use_llm:$('llm').checked});$('answer').textContent=j.answer+'\n\nMode: '+j.mode+(j.usage?.total_tokens?' · '+j.usage.total_tokens+' tokens':'');$('citations').replaceChildren(...j.citations.map(c=>el('span','',c.source)));}catch(e){$('answer').textContent=e.message;}finally{$('ask').disabled=false;}});
$('compare-quotes').addEventListener('click',async()=>{if(!current)return;const quotes=[...$('quote-inputs').children].map(row=>{const q={record_id:row.dataset.id,price_unit:row.dataset.unit};for(const i of row.querySelectorAll('input'))q[i.dataset.field]=i.value===''?null:Number(i.value);return q;});try{const j=await api('/api/quotes',{text:$('request').value,answers,quotes});$('quote-result').replaceChildren();for(const q of j.quotes){const d=el('p','section-copy',q.record_id+': '+(q.quoted_total_inr===null?money(q.known_subtotal_inr)+' known subtotal · missing '+q.missing_components.join(', '):money(q.quoted_total_inr)+' complete quoted total'));$('quote-result').append(d);}$('quote-result').append(el('p','hint',j.lowest_complete_quote?'Lowest entered total: '+j.lowest_complete_quote+'. Supplier confirmation is still required.':'A lowest complete quote is withheld until every entered quote includes tax and freight.'));}catch(e){$('quote-result').replaceChildren(el('p','error',e.message));}});
function tab(evaluation){$('workflow-view').classList.toggle('hidden',evaluation);$('evaluation-view').classList.toggle('hidden',!evaluation);$('workflow-nav').classList.toggle('active',!evaluation);$('evaluation-nav').classList.toggle('active',evaluation);window.scrollTo(0,0);}
$('workflow-nav').addEventListener('click',()=>tab(false));
$('evaluation-nav').addEventListener('click',async()=>{tab(true);try{const r=await api('/api/evaluation');$('evaluation-metrics').replaceChildren();if(!r.summary){$('evaluation-rows').replaceChildren();return;}metric($('evaluation-metrics'),r.summary.passed+'/'+r.summary.total,'SCENARIO CHECKS','Development regression suite');metric($('evaluation-metrics'),r.summary.constraint_violation_rate_percent+'%','SHORTLIST VIOLATIONS','Against authored compatible ID sets');metric($('evaluation-metrics'),r.summary.warm_latency_p95_ms+' ms','P95 WARM INFERENCE','Matching only; fitting excluded');$('evaluation-rows').replaceChildren(...r.scenarios.map(s=>{const tr=el('tr');for(const v of [s.id+' · '+s.label,s.expected_status,s.observed_status,s.passed?'PASS':'FAIL'])tr.append(el('td',v==='PASS'?'pass':v==='FAIL'?'fail':'',v));return tr;}));}catch(e){$('evaluation-rows').replaceChildren();$('error').textContent=e.message;}});
(async()=>{try{policies=await api('/api/policies');const h=await api('/api/health');$('llm').disabled=!h.llm_configured;$('llm-state').textContent=h.llm_configured?'(server configured)':'(server key + model required)';await analyze();}catch(e){$('error').textContent=e.message;}})();
