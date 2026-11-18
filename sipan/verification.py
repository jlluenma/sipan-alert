"""Preparación de consultas oficiales; no acredita identidades ni remitentes."""
import re
from datetime import datetime, timezone

SUNAT='https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias'
SBS='https://www.sbs.gob.pe/usuarios/aprende-con-la-sbs/modalidades-de-informalidad'

def verification_checks(text):
    from sipan.official_alerts import match_alerts
    rucs=list(dict.fromkeys(re.findall(r'(?<!\d)(?:10|15|17|20)\d{9}(?!\d)',text)))
    phones=list(dict.fromkeys(re.findall(r'(?<!\d)(?:\+51\s*)?9\d{2}[ -]?\d{3}[ -]?\d{3}(?!\d)',text)))
    domains=list(dict.fromkeys(re.findall(r'\b(?:https?://|www\.)[^\s<>]+',text)))
    checks=match_alerts(text)
    for ruc in rucs:
        total=sum(int(n)*w for n,w in zip(ruc[:10],[5,4,3,2,7,6,5,4,3,2]))
        digit=(11-total%11)%10
        valid=int(ruc[-1])==digit
        checks.append({'type':'RUC','value':ruc,'status':'Pendiente de consulta SUNAT' if valid else 'Dígito de control no válido','detail':'La validación matemática no confirma inscripción, estado activo ni identidad del remitente.','source':'SUNAT · Consulta RUC','url':SUNAT})
    for phone in phones:checks.append({'type':'Teléfono','value':phone,'status':'No verificado','detail':'Contrasta este número con el canal publicado por la empresa. No existe aquí una consulta automática de titularidad.','source':None,'url':None})
    for domain in domains:checks.append({'type':'Enlace del mensaje','value':domain,'status':'No verificado','detail':'No se ha abierto este enlace. Compara el dominio con el sitio oficial buscado independientemente.','source':None,'url':None})
    return {'checks':checks,'preparedAt':datetime.now(timezone.utc).isoformat(),'automaticVerification':False,'sources':[{'name':'SUNAT · Razón social y RUC','url':SUNAT},{'name':'SBS · Alertas de informalidad','url':SBS}],'notice':'Consulta asistida: todavía no se han obtenido registros externos de esta empresa. Un RUC válido no acredita al remitente del mensaje.'}
