"""Cruce determinista con una instantánea revisada de alertas SBS."""
import json
import re
from sipan.config import DATA_DIR
from sipan.preprocessing import strip_accents

def normalize(value):
    return re.sub(r'[^a-z0-9]+',' ',strip_accents(value.lower())).strip()

def match_alerts(message):
    catalog=json.loads((DATA_DIR/'sbs_alerts.json').read_text(encoding='utf-8'))
    normalized=' '+normalize(message)+' '
    matches=[]
    for entity in catalog['entities']:
        exact=next((entity[key] for key in ('package','domain') if entity.get(key) and re.search(r'(?<![\w.])'+re.escape(entity[key])+r'(?![\w.])',message,re.I)),None)
        name=next((name for name in [entity['name'],*entity.get('aliases',[])] if ' '+normalize(name)+' ' in normalized),None)
        if exact or name:
            matches.append({'type':'Antecedente oficial SBS','value':entity['name'],'status':'Identificador coincidente' if exact else 'Coincidencia de nombre; identidad por confirmar','detail':f"Mencionado en el comunicado SBS del {catalog['published_at']}. Cruce por: {exact or name}. {catalog['scope']}",'source':'SBS · '+catalog['title'],'url':catalog['source'],'publishedAt':catalog['published_at'],'reviewedAt':catalog['reviewed_at']})
    return matches
