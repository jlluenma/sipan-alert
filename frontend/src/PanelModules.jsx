import { useState } from 'react'
import DemoDashboard from './DemoDashboard'
import LearningSettings from './LearningSettings'
import UsersAdmin from './UsersAdmin'
import AccessPrototype from './AccessPrototype'
import ReviewPanel from './ReviewPanel'
import RealReports from './RealReports'
import LiveLearning from './LiveLearning'
import Community from './Community'

const examples = [
  {id:'A-7843',text:'Me pidieron depositar S/ [MONTO] para activar mi préstamo. Me dijeron que si no pago hoy pierdo la oferta.',state:'Pendiente'},
  {id:'A-7844',text:'La aplicación solicita acceso a todos mis contactos para aprobar el préstamo.',state:'Pendiente'},
  {id:'A-7845',text:'Me dijeron que avisarán a mis familiares si no pago antes de esta noche.',state:'Pendiente'},
  {id:'A-7846',text:'Me ofrecen un préstamo inmediato pero no entregan contrato ni detalle de los intereses.',state:'Pendiente'},
  {id:'A-7847',text:'Debo enviar fotos de mis documentos por un enlace desconocido para recibir el dinero.',state:'Pendiente'},
]
const categories=['Pago anticipado','Acceso invasivo','Amenaza o presión','Condiciones opacas']
export function PanelIcon({name}) {
  const paths={home:'M3 10 12 3l9 7M5 9v12h5v-7h4v7h5V9',reports:'M5 20V12m7 8V4m7 16V8',learning:'m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5',patterns:'M12 8V3M5 19l7-11 7 11M9 3h6M2 19h6m8 0h6',dataset:'M4 6c0-4 16-4 16 0s-16 4-16 0Zm0 0v12c0 4 16 4 16 0V6M4 12c0 4 16 4 16 0',users:'M8 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-6 10v-3a6 6 0 0 1 12 0v3m2-16a4 4 0 0 1 0 8m2 2a5 5 0 0 1 4 5',settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-6v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2'}
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"> <path d={paths[name]||paths.learning}/></svg>
}

export function Learning({rows,setRows,patterns=[],onReview}) {
  const [selected,setSelected]=useState(rows[0]?.id),[tab,setTab]=useState('Pendiente'),[note,setNote]=useState(''),[checked,setChecked]=useState([false,false,false,false]),[feedback,setFeedback]=useState(''),[duplicate,setDuplicate]=useState(false)
  const shown=rows.filter(r=>tab==='Pendiente'?r.state==='Pendiente':r.state!=='Pendiente')
  const current=shown.find(r=>r.id===selected)||shown[0]
  async function decide(state){try{if(onReview){await onReview(current,state,checked,note,duplicate);setFeedback('Décision de revisión guardada.')}else{setRows(rows.map(r=>r.id===current.id?{...r,state,note,labels:checked,duplicate}:r));setFeedback('Cambio de demostración.')}}catch(e){setFeedback(e.message)}}
return <><div className="module-stats">{[['reports','Pendientes',rows.filter(r=>r.state==='Pendiente').length],['learning','Validados',rows.filter(r=>r.state==='Validado').length],['patterns','Patrones candidatos',patterns.length]].map(([icon,title,value],i)=><article key={title} className={'stat-tone-'+i}><PanelIcon name={icon}/><div>{title}<strong>{value}</strong></div></article>)}</div><div className="learning-columns">
    <section className="module-card queue-card"><h2>Cola de revisión</h2><p>Reportes anonimizados que requieren revisión humana.</p><div className="queue-tabs">{['Pendiente','Revisados'].map(t=><button key={t} className={tab===t?'active':''} onClick={()=>setTab(t)}>{t==='Pendiente'?`Pendientes (${rows.filter(r=>r.state==='Pendiente').length})`:'Revisados'}</button>)}</div>{shown.map(r=><button className={'queue-message '+(current?.id===r.id?'active':'')} key={r.id} onClick={()=>{setSelected(r.id);setFeedback('');setNote(r.note||'');setChecked(r.labels||[false,false,false,false])}}><PanelIcon name="reports"/><div><b>Mensaje #{r.id}</b><p>{r.text.slice(0,90)}…</p></div><span className={`status-pill status-${r.state.toLowerCase()}`}>{r.state}</span></button>)}{!shown.length&&<p className="module-empty">No quedan ejemplos en esta bandeja.</p>}</section>
    <section className="module-card message-review"><h2>Revisión de mensaje</h2>{current?<><div className="review-heading"><b>Mensaje #{current.id}</b><span className={`status-pill status-${current.state.toLowerCase()}`}>{current.state}</span></div><div className="message-quote"><b>Texto del mensaje (anonimizado)</b><blockquote>“{current.text}”</blockquote></div><h3>Señales sugeridas</h3><p className="review-hint">Selecciona las categorías que corresponden al mensaje.</p><div className="category-grid">{categories.map((label,i)=><label key={label}><input type="checkbox" checked={checked[i]} onChange={e=>setChecked(checked.map((v,n)=>n===i?e.target.checked:v))}/>{label}</label>)}</div><label className="review-note">Observación del revisor/a<textarea maxLength={300} value={note} placeholder="Describe la razón de tu decisión…" onChange={e=>setNote(e.target.value)}/><small>{note.length} / 300</small></label><div className="review-controls"><label><input type="checkbox" checked={duplicate} onChange={e=>setDuplicate(e.target.checked)}/> Posible duplicado</label><button className="primary" onClick={()=>decide('Validado')}>Validar etiquetas</button><button className="secondary" onClick={()=>decide('Rechazado')}>Rechazar</button></div></>:<p>Selecciona un reporte de la cola.</p>}{feedback&&<p role="status" className="module-feedback">{feedback}</p>}</section>
    <section className="module-card pattern-column"><h2>Posibles patrones emergentes</h2><p>Agrupaciones de mensajes similares para evaluación.</p>{patterns.length?patterns.map(p=><article className="candidate-card" key={p.id}><h3><PanelIcon name="patterns"/>Patrón {p.id}</h3><div><span className="status-pill status-candidato">Para revisión humana</span><p>Mensajes del grupo: <b>{p.count}</b></p><p>Similitud promedio: <b>{Math.round(p.similarity*100)} %</b></p><h4>Términos frecuentes</h4><p>{p.common_terms.join(", ")}</p><aside>Patrón candidato; requiere validación humana.</aside></div></article>):<p className="module-empty">Aún no hay grupos candidatos.</p>}</section>
  </div></>
}

export default function PanelModules({section,user}) {
  const [rows,setRows]=useState(examples),[filter,setFilter]=useState(''),[role,setRole]=useState('revisor'),[notice,setNotice]=useState('')
  if(section==='home')return <DemoDashboard/>
  if(section==='community')return <Community moderation/>
  if(section==='learning')return <LiveLearning/>
  if(section==='reports')return <RealReports/>
  if(section==='patterns')return <RealReports patterns/>
  if(section==='users')return <div className="module-body"><AccessPrototype/></div>
  return <div className="module-body"><div className="module-demo">Datos mock · Las acciones de esta vista son una demostración local.</div>
    {section==='learning'&&<Learning rows={rows} setRows={setRows}/>}
    {section==='reports'&&<section className="module-card"><h2>Reportes ciudadanos</h2><input className="module-search" placeholder="Buscar por ID o mensaje" value={filter} onChange={e=>setFilter(e.target.value)}/><div className="module-table"><table><thead><tr><th>ID</th><th>Mensaje anonimizado</th><th>Estado</th></tr></thead><tbody>{rows.filter(r=>(r.id+r.text).toLowerCase().includes(filter.toLowerCase())).map(r=><tr key={r.id}><td>{r.id}</td><td>{r.text}</td><td><span className={`status-pill status-${r.state.toLowerCase()}`}>{r.state}</span></td></tr>)}</tbody></table></div></section>}
    {section==='patterns'&&<div className="pattern-grid">{['Pagos de activación','Acceso a contactos','Presión por vencimiento'].map((title,i)=><article className="module-card" key={title}><PanelIcon name="patterns"/><h2>P-0{i+1} · {title}</h2><span className="status-pill status-candidato">Candidato</span><p>{7+i*3} mensajes agrupados</p><p>Similitud de ejemplo: {92-i*7}%</p><p>Requiere revisión humana para interpretar el grupo.</p></article>)}</div>}
    {section==='dataset'&&<section className="module-card"><h2>Versiones del dataset</h2><p>Los pendientes y rechazados quedan excluidos del entrenamiento.</p><div className="module-table"><table><thead><tr><th>Versión</th><th>Validados</th><th>Entrenamiento</th><th>Evaluación</th><th>Procedencia</th></tr></thead><tbody>{['v1.2','v1.1','v1.0'].map((v,i)=><tr key={v}><td>{v}</td><td>{120-i*20}</td><td>80%</td><td>20%</td><td>Ejemplos mock revisados</td></tr>)}</tbody></table></div><button className="primary" onClick={()=>setNotice('Vista previa de nueva versión preparada en modo demostración. No se ha entrenado ningún modelo.')}>Preparar versión de ejemplo</button>{notice&&<p>{notice}</p>}</section>}
    {section==='users'&&<section className="module-card"><h2>Usuarios y permisos</h2><div className="module-table"><table><thead><tr><th>Cuenta de ejemplo</th><th>Rol</th><th>Estado</th></tr></thead><tbody>{[['Administrador','administrador'],['Revisor 01',role],['Usuario 01','usuario']].map(([name,r])=><tr key={name}><td>{name}</td><td>{name==='Revisor 01'?<select value={role} onChange={e=>setRole(e.target.value)}><option>revisor</option><option>usuario</option></select>:r}</td><td>Activo · Mock</td></tr>)}</tbody></table></div></section>}
    {section==='settings'&&<LearningSettings/>}
  </div>
}
