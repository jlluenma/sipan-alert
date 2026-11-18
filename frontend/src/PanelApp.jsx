import { useEffect, useState } from 'react'
import { api } from './api'
import ReviewPanel from './ReviewPanel'
import PanelModules, { PanelIcon } from './PanelModules'
import PanelNotifications from './PanelNotifications'
import './panel.css'

export default function PanelApp() {
  const [notifications,setNotifications] = useState(false)
  const [section,setSection] = useState('home'), [accountMenu,setAccountMenu] = useState(false)
const modules = [['home','Inicio'],['reports','Reportes'],['community','Comunidad'],['learning','Aprendizaje continuo'],['patterns','Patrones'],['dataset','Dataset evolutivo'],['users','Usuarios'],['settings','Configuración']]
  const [user,setUser] = useState(null), [ready,setReady] = useState(false)
  const [email,setEmail] = useState(''), [password,setPassword] = useState(''), [error,setError] = useState('')
  const authorized = account => account?.roles.some(role => ['administrador','revisor'].includes(role))
  useEffect(() => { api.me().then(account => {if(authorized(account)) setUser(account)}).finally(() => setReady(true)).catch(() => {}) }, [])
  async function login(event) {
    event.preventDefault(); setError('')
    try { const account=await api.login({email,password}); if(!authorized(account)) {await api.logout(); throw new Error('Esta cuenta no tiene acceso al panel interno.')} setUser(account); history.replaceState(null,'','/panel') } catch(err) {setError(err.message)}
  }
  async function logout() {await api.logout();setUser(null);history.replaceState(null,'','/panel/login')}
  if(!ready) return <main className="panel-access">Cargando panel…</main>
  if(!user) return <main className="panel-access"><form onSubmit={login}><img src="/logo-icon.png" alt="SipánAlert"/><h1>Acceso al panel interno</h1><p>Administración y revisión humana</p><label>Correo<input type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Contraseña<input type="password" required value={password} onChange={e=>setPassword(e.target.value)}/></label>{error&&<p className="error">{error}</p>}<button className="primary">Ingresar al panel</button></form></main>
return <div className="internal-panel"><aside className="panel-sidebar"><img src="/logo-white.png" alt="SipánAlert IA"/><nav>{modules.filter(([key])=>user.roles.includes('administrador')||!['users','dataset'].includes(key)).map(([key,title])=><button key={key} className={section===key?'module-active':''} onClick={()=>setSection(key)}><PanelIcon name={key}/>{title}</button>)}</nav><div className="sidebar-profile"><span className="profile-initials">{user.email.slice(0,2).toUpperCase()}</span><div><b>{user.roles.includes('administrador')?'Administrador':'Revisor/a'}</b><small>{user.email}</small><button onClick={logout}>Cerrar sesión</button></div></div></aside><div id="panel-content"><header className="panel-module-header"><div><h1>{section==='home'?'Panel de administración':modules.find(([key])=>key===section)?.[1]}</h1><p>{section==='learning'?'Revisa, valida y mejora los patrones de detección de posibles señales.':'Gestión de reportes y aprendizaje de SipánAlert'}</p></div><PanelNotifications user={user} onNavigate={setSection}/><div className="panel-account"><button onClick={()=>setAccountMenu(!accountMenu)}><span className="header-avatar">{user.email.slice(0,2).toUpperCase()}</span><span>{user.roles.includes('administrador')?'Administrador':'Revisor/a'} ▾</span></button>{accountMenu&&<div className="panel-account-menu"><p>{user.email}</p><button onClick={logout}>Cerrar sesión</button></div>}</div></header><PanelModules section={section} user={user}/></div></div>
}
