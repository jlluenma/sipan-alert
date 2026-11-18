const names={pago_anticipado:'Pago anticipado',acceso_invasivo:'Acceso invasivo',amenaza_presion:'Amenaza o presión',condiciones_opacas:'Condiciones opacas'}
export default function AnnotatedMessage({result}){
 const findings=[...result.signals.map(s=>({tag:'Señal identificada',tone:'observed',text:s.title})),...result.possibleSignals.map(s=>({tag:'Revisar',tone:'review',text:s.title}))]
 if(/pr[eé]stamo|cr[eé]dito|l[ií]nea|efectivo/i.test(result.analyzedText))findings.push({tag:'Revisar',tone:'review',text:'Oferta de crédito: verifica el remitente y las condiciones por canales oficiales.'})
 if(/responde|responda|contacta|asesor/i.test(result.analyzedText))findings.push({tag:'Revisar',tone:'review',text:'Invitación a iniciar contacto. Por sí sola no demuestra fraude.'})
 if(!result.signals.some(s=>s.label==='pago_anticipado')&&!result.possibleSignals.some(s=>s.label==='pago_anticipado'))findings.push({tag:'No identificada',tone:'neutral',text:'El analizador no detectó una solicitud de pago anticipado. Esto no acredita la seguridad de la oferta.'})
 const parts=[];let cursor=0
 for(const [index,h] of (result.highlights||[]).entries()){
  if(h.start<cursor||h.end>result.analyzedText.length)continue
  parts.push(result.analyzedText.slice(cursor,h.start))
  parts.push(<span className="annotated-fragment" key={index}><mark>{result.analyzedText.slice(h.start,h.end)}</mark><span className="analysis-tag">{names[h.label]||h.label}</span></span>)
  cursor=h.end
 }
 parts.push(result.analyzedText.slice(cursor))
 return <section className="analysis-text-card"><header><span className="sa-icon">description</span><b>Análisis del mensaje</b><span className="verification-label">Verificación necesaria</span></header><small className="provided-label">Texto proporcionado</small><blockquote>{parts}</blockquote><div className="analysis-findings"><h3>Señales y observaciones</h3><ul>{findings.map((finding,i)=><li key={i}><span className={'finding-label '+finding.tone}>{finding.tag}</span> {finding.text}</li>)}</ul></div><p>Este análisis describe señales del texto. La identidad del remitente y la legitimidad de la oferta requieren verificación externa.</p></section>
}
