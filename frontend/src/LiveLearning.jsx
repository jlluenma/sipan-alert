import {useEffect,useState} from 'react'
import {api} from './api'
import {Learning} from './PanelModules'
const keys=['pago_anticipado','acceso_invasivo','amenaza_presion','condiciones_opacas']
export default function LiveLearning(){
 const [rows,setRows]=useState([]),[patterns,setPatterns]=useState([]),[error,setError]=useState(''),[loading,setLoading]=useState(true)
 async function load(){try{const [reports,groups]=await Promise.all([api.reviewReports(),api.patterns()]);setRows(reports.map(r=>({...r,text:r.content,state:{pendiente:'Pendiente',validado:'Validado',rechazado:'Rechazado'}[r.status]||r.status,labels:keys.map(k=>Boolean(r.labels?.[k])),duplicate:Boolean(r.duplicate_of)})));setPatterns(groups);setError('')}catch(e){setError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load()},[])
 async function review(row,state,values,note,duplicate){if(duplicate&&!row.duplicate_of)throw new Error('Registra el ID del original antes de confirmar un duplicado.');await api.review(row.id,{decision:state==='Validado'?'validado':'rechazado',labels:Object.fromEntries(keys.map((k,i)=>[k,Number(values[i])])),note});await load()}
 return <div className="module-body">{error&&<p className="error" role="alert">{error}</p>}{loading&&<p>Cargando reportes…</p>}<Learning rows={rows} setRows={setRows} patterns={patterns} onReview={review}/></div>
}
