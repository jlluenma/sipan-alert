import { useEffect, useState } from 'react'
import { api } from './api'
import DemoDashboard from './DemoDashboard'

const categories = { pago_anticipado: 'Pago anticipado', acceso_invasivo: 'Acceso invasivo', amenaza_presion: 'Amenaza o presión', condiciones_opacas: 'Condiciones opacas' }

function Review({ report, reload }) {
  const [labels, setLabels] = useState(Object.fromEntries(Object.keys(categories).map(key => [key, report.labels?.[key] || 0])))
  const [note, setNote] = useState(''), [error, setError] = useState(''), [original, setOriginal] = useState('')
  async function save(decision) {
    try { await api.review(report.id, { decision, labels, note }); await reload() } catch (err) { setError(err.message) }
  }
  return <article className="review-item"><small>{report.id} · {report.status}</small><p>{report.content}</p>
    {Object.entries(categories).map(([key, title]) => <label key={key} style={{display:'block', margin:'8px 0'}}><input type="checkbox" checked={Boolean(labels[key])} onChange={e => setLabels({...labels, [key]: Number(e.target.checked)})} /> {title}</label>)}
    <label>Justificación<textarea value={note} onChange={e => setNote(e.target.value)} /></label>
    <div><button className="primary" onClick={() => save('validado')}>Validar categorías</button><button className="secondary" onClick={() => save('rechazado')}>Rechazar</button></div>
    <details><summary>Registrar duplicado</summary><input placeholder="ID del reporte original" value={original} onChange={e => setOriginal(e.target.value)} /><button onClick={async () => { try { await api.duplicate(report.id, original); reload() } catch (err) {setError(err.message)} }}>Guardar duplicado</button></details>
    {error && <p className="error">{error}</p>}</article>
}

export default function ReviewPanel({ user, go }) {
  const [selectedId, setSelectedId] = useState(null)
  const [reports, setReports] = useState([]), [patterns, setPatterns] = useState([]), [users, setUsers] = useState([])
  const [status, setStatus] = useState('pendiente'), [error, setError] = useState(''), [manifest, setManifest] = useState(null)
  const admin = user.roles.includes('administrador')
  async function load() {
    try { setReports(await api.reviewReports()); setPatterns(await api.patterns()); if (admin) setUsers(await api.users()) } catch (err) { setError(err.message) }
  }
  useEffect(() => { load() }, [])
  return <main className="page"><h1>Revisión y dataset · Datos reales</h1>
    <div className="metrics">{['pendiente','validado','rechazado'].map(state => <div key={state}><b>{reports.filter(r => r.status === state).length}</b><span>{state}</span></div>)}</div>
    <h2>Reportes</h2><div className="tabs">{['pendiente','validado','rechazado'].map(state => <button key={state} className={status === state ? 'active' : ''} onClick={() => setStatus(state)}>{state}</button>)}</div>
    <div className="review-workspace"><aside className="review-queue"><h2>Cola de revisión</h2>{reports.filter(r => r.status === status).map(report => <button className={selectedId === report.id ? 'selected' : ''} key={report.id} onClick={() => setSelectedId(report.id)}><b>Mensaje #{report.id.slice(0,8)}</b><span>{report.content?.slice(0,100)}</span><small>{report.status}</small></button>)}</aside><section className="review-detail"><h2>Revisión de mensaje</h2>{(() => {const report=reports.find(r => r.id === selectedId && r.status === status) || reports.find(r => r.status === status);return report ? <Review key={report.id} report={report} reload={load}/> : <p>Selecciona un reporte de la cola.</p>})()}</section></div>
    {!reports.some(r => r.status === status) && <p>No hay reportes en esta bandeja.</p>}
    <h2>Posibles patrones emergentes</h2><p>Grupos de mensajes similares para revisión humana. No confirman fraude.</p>
    {patterns.map(pattern => <article className="signal" key={pattern.id}><div><b>{pattern.id} · {pattern.count} aportes</b><p>{pattern.common_terms.join(', ')}</p></div></article>)}
    {patterns.length === 0 && <p>Aún no hay grupos candidatos.</p>}
    {admin && <><h2>Dataset evolutivo</h2><p>Solo incluye reportes validados, sin duplicados. No activa entrenamiento.</p><button className="primary" onClick={async () => { try {setManifest(await api.createDataset())} catch(err) {setError(err.message)} }}>Crear versión</button>{manifest && <pre>{JSON.stringify(manifest,null,2)}</pre>}
      <h2>Administración de roles</h2>{users.map(account => <article key={account.id} className="account-summary"><span>{account.email}<small> · {account.roles.join(', ')}</small></span><select defaultValue="" onChange={async e => { try { await api.grantRole(account.email,e.target.value); load() } catch(err) {setError(err.message)} }}><option value="" disabled>Agregar rol</option>{['usuario','revisor','administrador'].map(role => <option key={role}>{role}</option>)}</select></article>)}</>}
    {error && <p className="error">{error}</p>}</main>
}
