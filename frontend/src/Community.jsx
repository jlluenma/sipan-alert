import { useEffect, useState } from 'react'
import { request } from './api'
import { Interactions, OwnPublications, CommentModeration } from './CommunityTools'

export default function Community({ moderation = false }) {
  const [posts, setPosts] = useState([])
  const [alias, setAlias] = useState('')
  const [content, setContent] = useState('')
  const [consent, setConsent] = useState(false)
  const [message, setMessage] = useState('')
  const [composeOpen, setComposeOpen] = useState(false)
  const [topic,setTopic] = useState('Recientes')
  const topics={'Pagos anticipados':/pago|depos|activ|adelant/i,'Permisos invasivos':/contact|permiso|acceso/i,'Amenazas':/amenaz|presi|familiar/i}
  const visiblePosts=posts.filter(post=>!topics[topic]||topics[topic].test(post.content))

  async function load() {
    try {
      setPosts(await request('/community' + (moderation ? '/pending' : '')))
    } catch (error) {
      setMessage(error.message)
    }
  }

  useEffect(() => { load() }, [moderation])

  async function publish(event) {
    event.preventDefault()
    try {
      await request('/community', {
        method: 'POST',
        body: JSON.stringify({ alias, content, consent }),
      })
      setContent('')
      setConsent(false)
      setMessage('Publicación enviada a moderación.')
      setComposeOpen(false)
    } catch (error) {
      setMessage(error.message)
    }
  }

  async function review(id, status) {
    try {
      await request('/community/' + id + '/review', {
        method: 'POST',
        body: JSON.stringify({ status }),
      })
      await load()
    } catch (error) {
      setMessage(error.message)
    }
  }

  return (
    <section className={moderation ? 'module-body' : 'page community-feed'}>
      <h1>{moderation ? 'Moderación de comunidad' : 'Comunidad SipánAlert'}</h1>
      <p className="community-intro">Comparte experiencias y ayuda a otras personas a reconocer posibles riesgos.</p>
      {!moderation && <><aside className="community-rail"><h2>Tu comunidad</h2><a href="#community-posts"><span className="sa-icon">forum</span>Muro de experiencias</a><button onClick={() => setComposeOpen(true)}><span className="sa-icon">edit_square</span>Compartir experiencia</button><OwnPublications/><div className="community-guide"><b>Tu voz ayuda a prevenir</b><p>Comparte tu experiencia y ayuda a construir una comunidad más informada.</p></div></aside><div className="social-composer"><span className="social-avatar">Tú</span><button onClick={() => setComposeOpen(!composeOpen)}>¿Qué pasó con tu oferta de préstamo?</button><div className="composer-actions"><button onClick={()=>setComposeOpen(true)}><span className="sa-icon">edit</span>Escribir experiencia</button><span><span className="sa-icon">verified_user</span>Revisión antes de publicar</span><button className="primary" onClick={()=>setComposeOpen(true)}>Publicar</button></div></div><aside className="community-right"><section><h2>Conversaciones de la comunidad</h2><p>Explora experiencias por tema.</p>{Object.entries(topics).map(([name,regex])=><button key={name} onClick={()=>setTopic(name)}><span className="sa-icon">forum</span>{name}<b>{posts.filter(p=>regex.test(p.content)).length}</b></button>)}</section><section><h2>Antes de compartir</h2>{[['lock','Protege teléfonos, documentos y números de cuenta.'],['group','Comparte sin exponer a otras personas.'],['verified_user','Cuenta tu experiencia de forma clara y respetuosa.']].map(([icon,text])=><p className="community-tip" key={icon}><span className="sa-icon">{icon}</span>{text}</p>)}</section><section className="community-help"><h2>¿Necesitas orientación?</h2><p>Consulta tus dudas sobre ofertas de préstamo.</p><button className="primary" onClick={()=>document.querySelector('.chat-float[aria-expanded="false"]')?.click()}><span className="sa-icon">chat</span>Hablar con el asistente</button></section></aside></>}
      {!moderation && composeOpen && (
        <form className="community-compose" onSubmit={publish}>
          <h2>Comparte tu experiencia</h2><label>Alias público
            <input required minLength={2} maxLength={40} value={alias}
              onChange={event => setAlias(event.target.value)} />
          </label>
          <label>Tu experiencia
            <textarea required minLength={20} maxLength={1500} value={content}
              onChange={event => setContent(event.target.value)} />
          </label>
          <label>
            <input type="checkbox" required checked={consent}
              onChange={event => setConsent(event.target.checked)} />
            Autorizo publicar esta experiencia y he retirado nombres y datos personales.
          </label>
          <button className="primary">Enviar para revisión</button>
        </form>
      )}
      {message && <p role="status">{message}</p>}
      <div id="community-posts" className="social-posts">{!moderation&&<div className="social-filters">{['Recientes',...Object.keys(topics)].map(name=><button className={topic===name?'active':''} key={name} onClick={()=>setTopic(name)}>{name}</button>)}</div>}{visiblePosts.map(post => (
        <article className="community-post" key={post.id}>
          <header className="social-post-header"><span className="social-avatar">{post.alias.slice(0,2).toUpperCase()}</span><div><b>{post.alias}</b><small>{new Date(post.created_at).toLocaleDateString('es-PE')} · Comunidad</small></div><span className="social-approved">{moderation?'Pendiente':'✓ Revisado por moderación'}</span></header>
          <p>{post.content}</p>
          {!moderation && <Interactions id={post.id} />}
          {moderation && ['publicado', 'rechazado'].map(status => (
            <button key={status}
              className={status === 'publicado' ? 'primary' : 'secondary'}
              onClick={() => review(post.id, status)}>
              {status === 'publicado' ? 'Aprobar publicación' : 'Rechazar'}
            </button>
          ))}
        </article>
      ))}</div>
      {!posts.length && (
        <div className="community-empty"><h2>{moderation ? 'Todo al día' : 'Aquí comienzan las experiencias compartidas'}</h2><p>{moderation ? 'No hay publicaciones pendientes.' : 'Cuando se apruebe una publicación aparecerá en este muro.'}</p>{!moderation&&<button className="primary" onClick={()=>setComposeOpen(true)}>Comparte la primera experiencia</button>}</div>
      )}
      {moderation && <CommentModeration />}
    </section>
  )
}
