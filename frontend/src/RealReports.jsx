import {useEffect,useState} from 'react'
import {api} from './api'
export default function RealReports({patterns=false}){
 const [items,setItems]=useState([]),[error,setError]=useState('')
 useEffect(()=>{(patterns?api.patterns():api.reviewReports()).then(setItems).catch(e=>setError(e.message))},[patterns])
 return <section className="module-body"><div className="module-card"><h2>{patterns?'Patrones candidatos reales':'Reportes recibidos'}</h2>{error&&<p className="error">{error}</p>}{!error&&!items.length&&<p>No hay registros disponibles.</p>}{patterns?items.map(p=><article key={p.id}><h3>{p.id}</h3><p>{p.count} mensajes · {p.common_terms.join(', ')}</p><span className="status-pill status-candidato">Para revisión humana</span></article>):<div className="module-table"><table><thead><tr><th>ID</th><th>Mensaje anonimizado</th><th>Estado</th></tr></thead><tbody>{items.map(r=><tr key={r.id}><td>{r.id.slice(0,8)}</td><td>{r.content}</td><td><span className={`status-pill status-${r.status}`}>{r.status}</span></td></tr>)}</tbody></table></div>}</div></section>
}
