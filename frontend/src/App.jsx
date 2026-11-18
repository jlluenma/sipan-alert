import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import Panel from './ReviewPanel'
import HomeContent from './HomeContent'
import ChatText from './ChatText'
import Community from './Community'
import UserProfile from './UserProfile'
import AnnotatedMessage from './AnnotatedMessage'
import ExternalVerification from './ExternalVerification'
import ResultActions from './ResultActions'
import UserNotifications from './UserNotifications'
import EntityInvestigation from './EntityInvestigation'
import './analyzer-input.css'

const MAX_OFFER_LENGTH = 3000
const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const INPUT_MODES = [
  ['text', 'Por texto', 'edit'],
  ['photo', 'Por foto', 'image'],
  ['voice', 'Por voz', 'mic'],
]
const VOICE_ERRORS = {
  'not-allowed': 'Permite el acceso al micrófono en tu navegador e inténtalo de nuevo.',
  'service-not-allowed': 'Tu navegador bloqueó el dictado. Revisa sus permisos.',
  'audio-capture': 'No se pudo acceder al micrófono. Comprueba que esté conectado.',
  'no-speech': 'No se detectó voz. Intenta de nuevo y habla cerca del micrófono.',
  network: 'El dictado perdió la conexión. Inténtalo de nuevo.',
}

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
  const [reading, setReading] = useState('')
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [mode, setMode] = useState('text')
  const [dictating, setDictating] = useState('')
  const recognition = useRef(null)
  const photoPicker = useRef(null)
  const camera = useRef(null)
  const cameraVideo = useRef(null)
  const [cameraActive, setCameraActive] = useState(false)
  const [cameraReady, setCameraReady] = useState(false)
  const [captures, setCaptures] = useState([])
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  const tooLong = text.length > MAX_OFFER_LENGTH
  const busy = Boolean(reading || dictating) || submitting

  useEffect(() => () => {
    const session = recognition.current
    recognition.current = null
    session?.abort()
    const stream = camera.current
    camera.current = null
    stream?.getTracks?.().forEach(track => track.stop())
  }, [])

  useEffect(() => {
    if (cameraVideo.current && camera.current instanceof MediaStream) {
      cameraVideo.current.srcObject = camera.current
    }
  }, [cameraActive])

  function closeCamera() {
    const stream = camera.current
    camera.current = null
    stream?.getTracks?.().forEach(track => track.stop())
    setCameraActive(false)
    setCameraReady(false)
    setCaptures([])
  }

  async function openCamera() {
    if (!user) return onLogin()
    setError('')
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('La cámara requiere un navegador compatible y una conexión segura.')
      return
    }
    setCameraActive(true)
    const request = {}
    camera.current = request
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } } })
      if (camera.current !== request) {
        stream.getTracks().forEach(track => track.stop())
        return
      }
      camera.current = stream
      if (cameraVideo.current) cameraVideo.current.srcObject = stream
    } catch {
      if (camera.current !== request) return
      closeCamera()
      setError('No se pudo abrir la cámara. Revisa los permisos del navegador.')
    }
  }

  function takePhoto() {
    const video = cameraVideo.current
    if (!video?.videoWidth || captures.length >= 2) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    const preview = canvas.toDataURL('image/jpeg', 0.92)
    setCaptures(previous => [...previous, preview])
  }

  function readCaptures() {
    const photos = captures.map((preview, index) => ({
      source: preview,
      name: `foto ${index + 1}`,
    }))
    closeCamera()
    recognizePhotos(photos)
  }

  function changeMode(nextMode) {
    closeCamera()
    setMode(nextMode)
    setError('')
    setNotice('')
  }

  function startDictation() {
    if (!SpeechRecognition || busy || recognition.current) return
    setError('')
    setNotice('')
    const session = new SpeechRecognition()
    recognition.current = session
    session.lang = 'es-PE'
    session.onstart = () => {
      if (recognition.current === session) setDictating('Escuchando…')
    }
    session.onresult = event => {
      if (recognition.current !== session) return
      const spoken = event.results[event.resultIndex][0].transcript.trim()
      if (spoken) {
        setText(previous => [previous, spoken].filter(Boolean).join('\n\n'))
        setNotice('Revisa el texto dictado antes de analizar la oferta.')
      }
    }
    session.onerror = event => {
      if (recognition.current !== session) return
      setError(VOICE_ERRORS[event.error] || 'No se pudo transcribir la voz. Inténtalo de nuevo.')
    }
    session.onend = () => {
      if (recognition.current !== session) return
      recognition.current = null
      setDictating('')
    }
    try {
      session.start()
      setDictating('Activando micrófono…')
    } catch {
      recognition.current = null
      setError('No se pudo iniciar el dictado. Revisa el permiso del micrófono.')
    }
  }

  function stopDictation() {
    recognition.current?.stop()
    setDictating('Finalizando dictado…')
  }

  async function readPhotos(event) {
    const photos = Array.from(event.target.files)
    event.target.value = ''
    if (busy || !photos.length) return
    setError('')
    setNotice('')
    if (photos.length > 2) {
      setError('Selecciona como máximo dos fotos a la vez.')
      return
    }
    if (photos.some(photo => !PHOTO_TYPES.includes(photo.type))) {
      setError('Selecciona fotos en formato JPG, PNG o WebP.')
      return
    }
    recognizePhotos(photos.map(photo => ({ source: photo, name: photo.name })))
  }

  async function recognizePhotos(photos) {
    setError('')
    setNotice('')
    setReading('Preparando la lectura de fotos…')
    let worker
    const recognized = []
    const unreadable = []
    try {
      const { createWorker } = await import('tesseract.js')
      worker = await createWorker('spa')
      for (const [index, photo] of photos.entries()) {
        setReading(`Leyendo foto ${index + 1} de ${photos.length}…`)
        try {
          const { data } = await worker.recognize(photo.source)
          const extractedText = data.text.trim()
          if (extractedText) {
            recognized.push(extractedText)
            continue
          }
        } catch {
          // Keep any text extracted from the other photo.
        }
        unreadable.push(photo.name)
      }
      if (recognized.length) {
        setText(previous => [previous, ...recognized].filter(Boolean).join('\n\n'))
        setNotice('Revisa el texto extraído antes de analizar la oferta.')
      }
      if (unreadable.length) {
        setError(`No se pudo leer el texto de ${unreadable.join(', ')}. Prueba con una foto más nítida.`)
      }
    } catch {
      setError('No se pudo iniciar la lectura. Comprueba tu conexión e inténtalo de nuevo.')
    } finally {
      await worker?.terminate().catch(() => {})
      setReading('')
    }
  }

  async function submit(event) {
    event.preventDefault()
    if (busy || cameraActive || !text.trim() || tooLong) return
    setError('')
    setSubmitting(true)
    try {
      onResult(await api.analyze(text))
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return <section className="analyzer">
    <form onSubmit={submit}>
      <div className="analyzer__modes" role="group" aria-label="Cómo ingresar la oferta">
        {INPUT_MODES.map(([value, label, icon]) => <button
          key={value}
          type="button"
          aria-pressed={mode === value}
          disabled={busy}
          onClick={() => changeMode(value)}
        ><span className="sa-icon" aria-hidden="true">{icon}</span>{label}</button>)}
      </div>
      {mode === 'photo' && <div className="analyzer__source">
        <span className="analyzer__source-icon sa-icon" aria-hidden="true">add_photo_alternate</span>
        <div className="analyzer__source-copy">
          <strong>Sube tus fotos o capturas</strong>
          <small>Hasta 2 imágenes en JPG, PNG o WebP.</small>
        </div>
        <input
          ref={photoPicker}
          type="file"
          accept={PHOTO_TYPES.join(',')}
          multiple
          hidden
          onChange={readPhotos}
        />
        <div className="analyzer__source-actions">
          <button
            className="analyzer__source-action"
            type="button"
            disabled={busy || cameraActive}
            onClick={() => user ? photoPicker.current?.click() : onLogin()}
          >Elegir fotos</button>
          <button
            className="analyzer__source-action"
            type="button"
            disabled={busy || cameraActive}
            onClick={openCamera}
          >Usar cámara</button>
        </div>
      </div>}
      {mode === 'photo' && cameraActive && <div className="analyzer__camera">
        <video ref={cameraVideo} autoPlay muted playsInline onPlaying={() => setCameraReady(true)} aria-label="Vista previa de la cámara" />
        {!cameraReady && <small role="status">Esperando acceso a la cámara…</small>}
        {captures.length > 0 && <ul aria-label="Fotos tomadas">
          {captures.map((preview, index) => <li key={index}>
            <img src={preview} alt={`Foto ${index + 1}`} />
            <button type="button" className="analyzer__source-action" aria-label={`Quitar foto ${index + 1}`} onClick={() => setCaptures(previous => previous.filter((_, item) => item !== index))}>Quitar</button>
          </li>)}
        </ul>}
        <div className="analyzer__source-actions">
          <button className="analyzer__source-action" type="button" disabled={!cameraReady || captures.length >= 2} onClick={takePhoto}>Tomar foto</button>
          <button className="analyzer__source-action" type="button" disabled={!captures.length} onClick={readCaptures}>Leer {captures.length === 1 ? 'foto' : 'fotos'}</button>
          <button className="analyzer__source-action" type="button" onClick={closeCamera}>Cerrar cámara</button>
        </div>
      </div>}
      {mode === 'voice' && <div className={`analyzer__source${dictating ? ' analyzer__source--active' : ''}`}>
        <span className="analyzer__source-icon sa-icon" aria-hidden="true">{dictating ? 'graphic_eq' : 'mic'}</span>
        <div className="analyzer__source-copy">
          <strong>{dictating || 'Dicta la oferta'}</strong>
          <small>{SpeechRecognition ? 'Lee el mensaje en voz alta para convertirlo en texto.' : 'El dictado no está disponible en este navegador. Usa texto o foto.'}</small>
        </div>
        {SpeechRecognition && (
          <button
            className="analyzer__source-action"
            type="button"
            onClick={!user ? onLogin : dictating ? stopDictation : startDictation}
            disabled={submitting || Boolean(dictating && dictating !== 'Escuchando…')}
          >{dictating ? 'Detener dictado' : 'Iniciar dictado'}</button>
        )}
      </div>}
      {mode === 'voice' && SpeechRecognition && <small className="analyzer__privacy">El navegador puede usar un servicio en línea para transcribir.</small>}
      <div className="analyzer__status" role="status">
        {dictating ? <span className="analyzer__sr-only">{dictating}</span> : reading || notice}
      </div>
      {(mode === 'text' || text) && <textarea
        aria-label="Texto de la oferta"
        value={text}
        onChange={event => setText(event.target.value)}
        placeholder={user ? 'Escribe o pega aquí el texto de la oferta…' : 'Inicia sesión para escribir o pegar el texto de la oferta.'}
        maxLength={tooLong ? undefined : MAX_OFFER_LENGTH}
        readOnly={busy}
        disabled={!user}
        required
      />}
      {tooLong && <p className="error" role="alert">El texto tiene {text.length} caracteres. Redúcelo a {MAX_OFFER_LENGTH} o menos para analizarlo.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {user ? <div className="analyzer__actions">
        <span>🔒 No incluyas datos personales.</span>
        <button className="primary" type="submit" disabled={busy || cameraActive || tooLong || !text.trim()}>
          {submitting ? 'Analizando…' : 'Analizar oferta →'}
        </button>
      </div> : mode === 'text' && <button className="login-cta" type="button" onClick={onLogin}>Iniciar sesión para analizar</button>}
    </form>
  </section>
}

function Result({ result, onBack, user }) {
  const [consent, setConsent] = useState(false); const [report, setReport] = useState(null); const [error, setError] = useState('')
  const all = [...result.signals, ...result.possibleSignals]
  async function submitReport() { setError(''); try { setReport(await api.report(result.analyzedText)) } catch (err) { setError(err.message) } }
return <main className="page result"><button className="link-button" onClick={onBack}>← Nuevo análisis</button><p className="eyebrow">RESULTADO ORIENTATIVO</p><h1>{all.length ? `Encontramos ${all.length} posible${all.length > 1 ? 's' : ''} señal${all.length > 1 ? 'es' : ''}` : 'Verificación necesaria'}</h1><p className="muted">{result.modelAvailable ? 'Resultado combinado con reglas y modelo.' : 'El modelo no está disponible; se aplicaron las reglas documentadas.'}</p><AnnotatedMessage result={result}/><ExternalVerification verification={result.verification}/>{all.map(signal => <article className="signal" key={signal.label}><span className="signal__icon">!</span><div><h2>{result.possibleSignals.includes(signal) ? 'Posible: ' : ''}{signal.title}</h2><p>{signal.explanation}</p><small>{signal.source} · confianza {signal.confidence}</small><p><b>Qué hacer:</b> {signal.recommendations[0]}</p></div></article>)}<ResultActions result={result}/><section className="report-card"><h2>¿Quieres reportar esta oferta a SipánAlert?</h2><p>Un revisor humano evaluará el aporte. Esto no es una denuncia oficial ni confirma fraude.</p>{user ? <>{!report ? <><label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} /> Autorizo guardar el texto anonimizado para revisión humana.</label><button className="primary" disabled={!consent} onClick={submitReport}>⚑ Reportar para revisión</button></> : <div className="success"><b>Reporte recibido.</b><br />Código de eliminación: <code>{report.deletionCode}</code></div>}</> : <p className="error">Inicia sesión para reportar esta oferta.</p>}{error && <p className="error">{error}</p>}</section></main>
}

function Account({ user, onAuth, onLogout, go, initialTab }) {
  const [reports, setReports] = useState([])
  useEffect(() => { if (user) api.myReports().then(setReports).catch(() => setReports([])) }, [user])
  if (!user) return <main className="page account"><h1>Cuenta</h1><p className="muted">Accede para analizar y consultar tus aportes.</p><AuthForm onAuthenticated={onAuth} /></main>
  return <UserProfile key={initialTab.revision} user={user} onLogout={onLogout} go={go} initialTab={initialTab.name}/>
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
  const messageList = useRef(null)
  const launcher = useRef(null)

  useEffect(() => {
    const list = messageList.current
    if (list) list.scrollTop = list.scrollHeight
  }, [open, messages, loading])

  function closeChat() {
    setOpen(false)
    launcher.current?.focus()
  }

  return <aside className="chat-widget" onKeyDown={event => {
    if (event.key === 'Escape' && open) closeChat()
  }}>
    {open && <section id="sipanchat" className="chat-window" aria-labelledby="sipanchat-title">
      <header>
        <span className="sa-icon chat-mark" aria-hidden="true">shield</span>
        <div>
          <h2 id="sipanchat-title">Asistente SipánAlert</h2>
          <small>Orientación sobre ofertas de préstamo</small>
        </div>
        <button type="button" onClick={closeChat} aria-label="Cerrar asistente">
          <span className="sa-icon" aria-hidden="true">close</span>
        </button>
      </header>
      <div className="chat-messages" ref={messageList} role="log" aria-label="Conversación">
        {messages.map((item, index) => <div key={index} className={`chat-message chat-message--${item.role}`}>
          <ChatText text={item.text} />
          {item.fallback && <small>Respuesta del catálogo local</small>}
        </div>)}
        {loading && <p className="chat-message chat-message--bot chat-typing">Escribiendo…</p>}
        {source && <a className="chat-source" href={source.url} target="_blank" rel="noreferrer">
          <span className="sa-icon" aria-hidden="true">open_in_new</span>Consultar {source.name}
        </a>}
        {choices.length > 0 && !loading && <div className="chat-choices">
          {choices.map(choice => <button key={choice} type="button" onClick={() => send(choice)}>{choice}</button>)}
        </div>}
      </div>
      <form onSubmit={event => { event.preventDefault(); send() }}>
        <input aria-label="Tu pregunta" value={question} onChange={event => setQuestion(event.target.value)}
          maxLength={400} placeholder="Escribe tu pregunta" />
        <button className="primary" type="submit" aria-label="Enviar" disabled={loading || !question.trim()}>
          <span className="sa-icon" aria-hidden="true">arrow_upward</span>
        </button>
      </form>
      <footer>Evita compartir datos personales.</footer>
    </section>}
    <button ref={launcher} className="chat-float" type="button" onClick={() => setOpen(value => !value)}
      aria-expanded={open} aria-label={open ? 'Cerrar asistente' : 'Abrir asistente'}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
        strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {open ? <path d="m6 6 12 12M18 6 6 18" /> : <>
          <path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H6l-4 2 2-6v-4.5A8.5 8.5 0 0 1 12.5 3 8.5 8.5 0 0 1 21 11.5Z" />
          <path d="M8 12h.01M12 12h.01M16 12h.01" />
        </>}
      </svg>
    </button>
  </aside>
}

export default function App() {
  const [user, setUser] = useState(null), [view, setView] = useState('home'), [result, setResult] = useState(null), [showLogin, setShowLogin] = useState(false)
  useEffect(() => { api.me().then(setUser).catch(() => setUser(null)) }, [])
  const [welcome,setWelcome] = useState('')
  const [accountTab, setAccountTab] = useState({ name: 'profile', revision: 0 })
  function openAccount(tab = 'profile') {
    setAccountTab(previous => ({ name: tab, revision: previous.revision + 1 }))
    setView('account')
  }
  useEffect(()=>{if(!welcome)return;const timer=setTimeout(()=>setWelcome(''),4500);return()=>clearTimeout(timer)},[welcome])
  function authenticated(account) { setWelcome(account.name ? `Bienvenido/a, ${account.name}` : 'Bienvenido/a a SipánAlert'); setUser(account); setShowLogin(false); if (account.roles.includes('administrador') || account.roles.includes('revisor')) window.location.assign('/panel') }
  async function logout() { await api.logout(); setUser(null); setView('home') }
return <><header className="nav"><button className="brand" onClick={() => setView('home')}><img src="/logo-icon.png" alt="" />Sipán<span>Alert</span><sup>IA</sup></button><nav><button onClick={() => setView('home')}>Inicio</button><button onClick={()=>setView('community')}>Comunidad</button><button onClick={() => setView("investigation")}>Investigar entidad</button><UserNotifications key={user?.id || 'guest'} user={user} onLogin={() => setShowLogin(true)} onNavigate={openAccount}/><button onClick={() => user ? openAccount() : setShowLogin(true)}><span className="sa-icon" aria-hidden="true">account_circle</span> {user ? (user.name || user.email) : 'Iniciar sesión'}</button></nav></header>{view === 'home' && <><main className="hero" id="top"><p className="eyebrow">PREVENCIÓN FINANCIERA INTELIGENTE</p><h1>¿Recibiste una oferta de préstamo?</h1><p>Ingresa la oferta por texto, foto o voz y revisa posibles riesgos antes de pagar o compartir información.</p><Analyzer user={user} onLogin={() => setShowLogin(true)} onResult={(r) => { setResult(r); setView('result') }} /></main><HomeContent /></>}{view === 'investigation' && <EntityInvestigation user={user} onLogin={() => setShowLogin(true)} onCommunity={() => setView('community')} onAnalyze={() => setView('home')} />}{view==='community'&&<Community/>}{view === 'result' && <Result result={result} user={user} onBack={() => setView('home')} />}{view === 'account' && <Account user={user} onAuth={authenticated} onLogout={logout} go={setView} initialTab={accountTab} />}{view === 'panel' && user && <Panel user={user} go={setView} />}{showLogin && <div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true" aria-label="Iniciar sesión"><button className="modal__close" onClick={() => setShowLogin(false)}>×</button><h2>Bienvenido a SipánAlert</h2><p className="login-description">Inicia sesión para analizar ofertas y consultar tus reportes.</p><AuthForm compact onAuthenticated={authenticated} /></div></div>}<ChatWidget />{welcome&&<div className="welcome-toast" role="status"><span>✓</span>{welcome}<button aria-label="Cerrar bienvenida" onClick={()=>setWelcome('')}>×</button></div>}</>
}
