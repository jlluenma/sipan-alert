import { useEffect, useState } from 'react'
import { api } from './api'
import Panel from './ReviewPanel'
import HomeContent from './HomeContent'
import ChatText from './ChatText'
import Community from './Community'
import UserProfile from './UserProfile'
import AnnotatedMessage from './AnnotatedMessage'
import ExternalVerification from './ExternalVerification'

const labels = {
  pago_anticipado: 'Pago por adelantado', acceso_invasivo: 'Acceso invasivo',
  amenaza_presion: 'Amenaza o presión', condiciones_opacas: 'Condiciones ocultas',
}

function AuthForm({ onAuthenticated, compact = false }) {
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setError('')
    if (mode === 'register' && password !== repeat) return setError('Las contraseñas no coinciden.')
    try { onAuthenticated(await (mode === 'login' ? api.login({ email, password }) : api.register({ email, password, name }))) }
    catch (err) { setError(err.message) }
  }
  return <section className={`auth-card ${compact ? 'auth-card--compact' : ''}`}>
    <div className="tabs"><button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Iniciar sesión</button><button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Crear cuenta</button></div>
    <form onSubmit={submit}>{mode==='register'&&<label>Nombre<input required maxLength={80} autoComplete="name" value={name} onChange={e=>setName(e.target.value)}/></label>}<label>Correo<input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="nombre@correo.com" /></label><label>Contraseña<input type="password" required minLength="10" value={password} onChange={e => setPassword(e.target.value)} /></label>{mode === 'register' && <label>Repite la contraseña<input type="password" required minLength="10" value={repeat} onChange={e => setRepeat(e.target.value)} /></label>}{error && <p className="error">{error}</p>}<button className="primary" type="submit">{mode === 'login' ? 'Ingresar' : 'Crear cuenta'}</button></form>
  </section>
}

function Analyzer({ user, onLogin, onResult }) {
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  async function submit(event) { event.preventDefault(); setError(''); try { onResult(await api.analyze(text)) } catch (err) { setError(err.message) } }
  return <section className="analyzer">{!user ? <><textarea disabled placeholder="Inicia sesión para pegar el mensaje y revisarlo." /><button className="login-cta" onClick={() => onLogin()}>⇥ Iniciar sesión para escribir</button></> : <form onSubmit={submit}><textarea value={text} onChange={e => setText(e.target.value)} placeholder="Pega aquí el texto de la oferta…" maxLength="3000" required /><div className="analyzer__actions"><span>🔒 No incluyas datos personales.</span><button className="primary">Analizar oferta →</button></div>{error && <p className="error">{error}</p>}</form>}</section>
}

function Result({ result, onBack, user }) {
  const [consent, setConsent] = useState(false); const [report, setReport] = useState(null); const [error, setError] = useState('')
  const all = [...result.signals, ...result.possibleSignals]
  async function submitReport() { setError(''); try { setReport(await api.report(result.analyzedText)) } catch (err) { setError(err.message) } }
return <main className="page result"><button className="link-button" onClick={onBack}>← Nuevo análisis</button><p className="eyebrow">RESULTADO ORIENTATIVO</p><h1>{all.length ? `Encontramos ${all.length} posible${all.length > 1 ? 's' : ''} señal${all.length > 1 ? 'es' : ''}` : 'Verificación necesaria'}</h1><p className="muted">{result.modelAvailable ? 'Resultado combinado con reglas y modelo.' : 'El modelo no está disponible; se aplicaron las reglas documentadas.'}</p><AnnotatedMessage result={result}/><ExternalVerification verification={result.verification}/>{all.map(signal => <article className="signal" key={signal.label}><span className="signal__icon">!</span><div><h2>{result.possibleSignals.includes(signal) ? 'Posible: ' : ''}{signal.title}</h2><p>{signal.explanation}</p><small>{signal.source} · confianza {signal.confidence}</small><p><b>Qué hacer:</b> {signal.recommendations[0]}</p></div></article>)}<section className="report-card"><h2>¿Quieres reportar esta oferta a SipánAlert?</h2><p>Un revisor humano evaluará el aporte. Esto no es una denuncia oficial ni confirma fraude.</p>{user ? <>{!report ? <><label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> Autorizo guardar el texto anonimizado para revisión humana.</label><button className="primary" disabled={!consent} onClick={submitReport}>⚑ Reportar para revisión</button></> : <div className="success"><b>Reporte recibido.</b><br />Código de eliminación: <code>{report.deletionCode}</code></div>}</> : <p className="error">Inicia sesión para reportar esta oferta.</p>}{error && <p className="error">{error}</p>}</section></main>
}

function Account({ user, onAuth, onLogout, go }) {
  const [reports, setReports] = useState([])
  useEffect(() => { if (user) api.myReports().then(setReports).catch(() => setReports([])) }, [user])
  if (!user) return <main className="page account"><h1>Cuenta</h1><p className="muted">Accede para analizar y consultar tus aportes.</p><AuthForm onAuthenticated={onAuth} /></main>
  return <UserProfile user={user} onLogout={onLogout} go={go}/>
  const staff = user.roles.includes('administrador') || user.roles.includes('revisor')
  return <main className="page account"><h1>Cuenta</h1><div className="account-summary"><b>{user.email}</b><span>{user.roles.join(' · ')}</span></div>{staff && <button className="primary" onClick={() => go('panel')}>⚙ Abrir panel de {user.roles.includes('administrador') ? 'administración' : 'revisión'}</button>}<h2>Mis reportes</h2>{reports.length ? <ul className="report-list">{reports.map(r => <li key={r.id}><code>{r.id.slice(0, 8)}</code><span>{r.estado}</span></li>)}</ul> : <p className="muted">Aún no enviaste reportes.</p>}<button className="link-button" onClick={onLogout}>Cerrar sesión</button></main>
}

function LegacyPanel({ user, go }) {
  const [reports, setReports] = useState([]); const [error, setError] = useState('')
  async function load() { try { setReports(await api.reviewReports()) } catch (err) { setError(err.message) } }
  useEffect(() => { load() }, [])
  const pending = reports.filter(r => r.status === 'pendiente')
  async function review(report, decision) { const values = Object.fromEntries(Object.keys(labels).map(key => [key, 0])); try { await api.review(report.id, { decision, labels: values, note: '' }); await load() } catch (err) { setError(err.message) } }
  return <main className="page panel"><button className="link-button" onClick={() => go('account')}>← Cuenta</button><p className="eyebrow">{user.roles.includes('administrador') ? 'ADMINISTRACIÓN' : 'REVISIÓN HUMANA'}</p><h1>{user.roles.includes('administrador') ? 'Panel de administración' : 'Panel de revisión'}</h1><div className="metrics"><div><b>{pending.length}</b><span>Pendientes</span></div><div><b>{reports.filter(r => r.status === 'validado').length}</b><span>Validados</span></div><div><b>{reports.filter(r => r.status === 'rechazado').length}</b><span>Rechazados</span></div></div><h2>Bandeja de revisión</h2>{pending.length ? pending.map(r => <article className="review-item" key={r.id}><p>{r.content}</p><small>{r.id}</small><div><button className="primary" onClick={() => review(r, 'validado')}>Validar</button><button className="secondary" onClick={() => review(r, 'rechazado')}>Rechazar</button></div></article>) : <p className="muted">No hay reportes pendientes.</p>}{error && <p className="error">{error}</p>}</main>
}

function ChatWidget() {
  const [topic, setTopic] = useState(null)
  const [open, setOpen] = useState(false), [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Hola, soy el asistente de SipánAlert. ¿Qué ocurrió con la oferta?' }])
  const [choices, setChoices] = useState([]), [loading, setLoading] = useState(false), [source, setSource] = useState(null)
  useEffect(() => { api.chatTopics().then(data => { setMessages([{ role: 'bot', text: data.message }]); setChoices(data.choices) }).catch(() => {}) }, [])
  async function send(value = question) {
    const content = value.trim(); if (!content || loading) return
    setMessages(items => [...items, { role: 'user', text: content }]); setQuestion(''); setLoading(true)
    try { const reply = await api.chat(content, topic); setTopic(reply.topic); setMessages(items => [...items, { role: 'bot', text: reply.message, fallback: reply.provider === 'local' }]); setChoices((reply.choices || []).map(choice => Array.isArray(choice) ? choice[0] : choice)); setSource(reply.sourceUrl ? { name: reply.sourceName, url: reply.sourceUrl } : null) }
    catch { setMessages(items => [...items, { role: 'bot', text: 'No pude responder ahora. Si hay amenazas, guarda evidencia y llama al 1818.', fallback: true }]) }
    finally { setLoading(false) }
  }
return <aside className="chat-widget">{open && <section className="chat-window"><header><div><b>Asistente SipánAlert</b><small>Orientación preventiva</small></div><button onClick={() => setOpen(false)} aria-label="Cerrar">×</button></header><div className="chat-messages">{messages.map((item, index) => <div key={index} className={`chat-message chat-message--${item.role}`}><ChatText text={item.text} />{item.fallback && <small>Respuesta del catálogo local</small>}</div>)}{loading && <p className="chat-message chat-message--bot">Escribiendo…</p>}</div>{choices.length > 0 && <div className="chat-choices">{choices.map(choice => <button key={choice} onClick={() => send(choice)}>{choice}</button>)}</div>}{source && <a className="chat-source" href={source.url} target="_blank" rel="noreferrer">Consultar {source.name}</a>}<form onSubmit={event => { event.preventDefault(); send() }}><input value={question} onChange={event => setQuestion(event.target.value)} maxLength="400" placeholder="Escribe tu pregunta" /><button className="primary" aria-label="Enviar">↑</button></form><footer>No incluyas datos personales. No reemplaza una denuncia oficial.</footer></section>}<button className="chat-float" onClick={() => setOpen(value => !value)} aria-expanded={open} aria-label={open ? 'Cerrar asistente' : 'Abrir asistente'}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{open ? <path d="m6 6 12 12M18 6 6 18"/> : <><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H6l-4 2 2-6v-4.5A8.5 8.5 0 0 1 12.5 3 8.5 8.5 0 0 1 21 11.5Z"/><path d="M8 12h.01M12 12h.01M16 12h.01"/></>}</svg></button></aside>
}

export default function App() {
  const [user, setUser] = useState(null), [view, setView] = useState('home'), [result, setResult] = useState(null), [showLogin, setShowLogin] = useState(false)
  useEffect(() => { api.me().then(setUser).catch(() => setUser(null)) }, [])
  const [welcome,setWelcome] = useState('')
  useEffect(()=>{if(!welcome)return;const timer=setTimeout(()=>setWelcome(''),4500);return()=>clearTimeout(timer)},[welcome])
  function authenticated(account) { setWelcome(account.name ? `Bienvenido/a, ${account.name}` : 'Bienvenido/a a SipánAlert'); setUser(account); setShowLogin(false); if (account.roles.includes('administrador') || account.roles.includes('revisor')) window.location.assign('/panel') }
  async function logout() { await api.logout(); setUser(null); setView('home') }
return <><header className="nav"><button className="brand" onClick={() => setView('home')}><img src="/logo-icon.png" alt="" />Sipán<span>Alert</span><sup>IA</sup></button><nav><button onClick={() => setView('home')}>Inicio</button><button onClick={()=>setView('community')}>Comunidad</button><a href="/#como-funciona">Cómo funciona</a><a href="/#ejemplo-analisis">Ver ejemplo</a><button onClick={() => user ? setView('account') : setShowLogin(true)}><span className="sa-icon" aria-hidden="true">account_circle</span> {user ? (user.name || user.email) : 'Iniciar sesión'}</button></nav></header>{view === 'home' && <><main className="hero" id="top"><p className="eyebrow">PREVENCIÓN FINANCIERA INTELIGENTE</p><h1>¿Recibiste una oferta de préstamo?</h1><p>Pega el texto y revisa posibles riesgos antes de pagar o compartir información.</p><Analyzer user={user} onLogin={() => setShowLogin(true)} onResult={(r) => { setResult(r); setView('result') }} /></main><HomeContent /></>}{view==='community'&&<Community/>}{view === 'result' && <Result result={result} user={user} onBack={() => setView('home')} />}{view === 'account' && <Account user={user} onAuth={authenticated} onLogout={logout} go={setView} />}{view === 'panel' && user && <Panel user={user} go={setView} />}{showLogin && <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-label="Iniciar sesión"><button className="modal__close" onClick={() => setShowLogin(false)}>×</button><h2>Bienvenido a SipánAlert</h2><p className="login-description">Inicia sesión para analizar ofertas y consultar tus reportes.</p><AuthForm compact onAuthenticated={authenticated} /></div></div>}<ChatWidget />{welcome&&<div className="welcome-toast" role="status"><span>✓</span>{welcome}<button aria-label="Cerrar bienvenida" onClick={()=>setWelcome('')}>×</button></div>}</>
}
