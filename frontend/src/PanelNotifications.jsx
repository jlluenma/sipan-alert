import { useEffect, useState } from 'react'
import { api } from './api'

export default function PanelNotifications({user,onNavigate}) {
  const [open,setOpen]=useState(false),[items,setItems]=useState([]),[error,setError]=useState('')
  const key=`sipan-notifications-read-${user.id}`
  const [read,setRead]=useState(()=>{try{return JSON.parse(localStorage.getItem(key)||'[]')}catch{return []}})
  async function load(){
    try {
      const [reports,patterns]=await Promise.all([api.reviewReports(),api.patterns()])
      const pending=reports.filter(r=>r.status==='pendiente')
      const next=[]
      if(pending.length)next.push({id:`pending-${pending.length}-${pending[0].id}`,title:`${pending.length} reportes pendientes`,text:'Revisa los aportes que esperan validación humana.',target:'learning'})
      const duplicates=pending.filter(r=>r.duplicate_of)
      if(duplicates.length)next.push({id:`duplicates-${duplicates.map(r=>r.id).sort().join('-')}`,title:`${duplicates.length} posibles duplicados`,text:'Comprueba si corresponden a un reporte anterior.',target:'reports'})
      if(patterns.length)next.push({id:`patterns-${patterns.map(p=>p.id).sort().join('-')}`,title:`${patterns.length} patrones candidatos`,text:'Agrupaciones para revisión; no son casos confirmados.',target:'patterns'})
      if(user.roles.includes('administrador')&&pending.length>=10)next.push({id:`backlog-${pending.length}`,title:'Acumulación de reportes pendientes',text:'La bandeja tiene diez o más aportes por revisar.',target:'learning'})
      setItems(next);setError('')
    } catch {setError('No se pudieron consultar las notificaciones. Puedes volver a intentarlo.')}
  }
  useEffect(()=>{load()},[])
  function mark(id){const next=[...new Set([...read,id])];setRead(next);localStorage.setItem(key,JSON.stringify(next))}
  const unread=items.filter(item=>!read.includes(item.id)).length
  return <div className="header-notifications"><button aria-label={`Notificaciones, ${unread} sin leer`} aria-expanded={open} onClick={()=>{setOpen(!open);if(!open)load()}}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>{unread>0&&<span className="notification-count">{unread}</span>}</button>{open&&<section className="notification-menu"><b>Notificaciones</b>{error?<p role="alert">{error}</p>:items.length?items.map(item=><button className={'notification-item '+(!read.includes(item.id)?'unread':'')} key={item.id} onClick={()=>{mark(item.id);onNavigate(item.target);setOpen(false)}}><strong>{item.title}</strong><span>{item.text}</span></button>):<p>No hay tareas pendientes para notificar.</p>}<button className="notification-refresh" onClick={load}>Actualizar</button></section>}</div>
}
