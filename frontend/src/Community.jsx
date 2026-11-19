import { useEffect, useRef, useState } from 'react'
import { communityPhotoUrl, request } from './api'
import { Interactions, OwnPublications, CommentModeration } from './CommunityTools'
import './community-photos.css'
import './community-details.css'

const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_PHOTO_BYTES = 5 * 1024 * 1024
const TOPICS = {
  'Pagos anticipados': /pago|depos|activaci[oó]n|adelant/i,
  'Permisos invasivos': /contactos|permisos|acceso|datos personales/i,
  'Amenazas': /amenaz|extorsi[oó]n|intimid/i,
  'Suplantación': /suplant|se (?:hizo|hac[ií]a) pasar|falso|falsa/i,
}
const normalizeSearch = value => value.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
const postDate = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeZone: 'America/Lima' })

function PostDetail({ post, onClose }) {
  const dialog = useRef(null)
  useEffect(() => {
    dialog.current.showModal()
  }, [])
  const topics = Object.entries(TOPICS).filter(([, matches]) => matches.test(post.content)).map(([name]) => name)
  return <dialog ref={dialog} className="community-detail" aria-labelledby="community-detail-title" onClose={onClose}>
    <header>
      <h2 id="community-detail-title">Detalle de la experiencia</h2>
      <button type="button" aria-label="Cerrar detalle" onClick={() => dialog.current.close()}>×</button>
    </header>
    <div className="community-detail__author">
      <span className="social-avatar">{post.alias.slice(0, 2).toUpperCase()}</span>
      <div><strong>{post.alias}</strong><br /><time dateTime={post.created_at}>{postDate.format(new Date(post.created_at))}</time></div>
    </div>
    <p className="social-approved">Revisado por moderación</p>
    <p>La moderación revisa que la publicación cumpla las reglas del muro. La experiencia corresponde a su autor.</p>
    {topics.length > 0 && <ul className="community-detail__topics" aria-label="Temas relacionados">
      {topics.map(topic => <li key={topic}>{topic}</li>)}
    </ul>}
    <p className="community-detail__content">{post.content}</p>
    {post.photos?.length > 0 && <>
      <h3>Fotos adjuntas</h3>
      <div className="community-post-photos">{post.photos.map(position => <img key={position}
        src={communityPhotoUrl(post.id, position, false)} alt={`Foto ${position} de la experiencia`} />)}</div>
    </>}
    <button className="secondary" type="button" onClick={() => dialog.current.close()}>Volver al muro</button>
  </dialog>
}

function encodePhoto(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',', 2)[1])
    reader.onerror = () => reject(new Error('No se pudo leer la foto seleccionada.'))
    reader.readAsDataURL(file)
  })
}

function PhotoPreview({ file, position, onRemove, disabled }) {
  const [url, setUrl] = useState('')
  useEffect(() => {
    const objectUrl = URL.createObjectURL(file)
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [file])
  return <li>
    {url && <img src={url} alt={`Vista previa de la foto ${position}`} />}
    <button
      className="community-attachments__remove"
      type="button"
      disabled={disabled}
      aria-label={`Quitar foto ${position}`}
      title="Quitar foto"
      onClick={onRemove}
    ><span aria-hidden="true">×</span></button>
  </li>
}

export default function Community({ moderation = false }) {
  const [posts, setPosts] = useState([])
  const [alias, setAlias] = useState('')
  const [content, setContent] = useState('')
  const [consent, setConsent] = useState(false)
  const [message, setMessage] = useState('')
  const [composeOpen, setComposeOpen] = useState(false)
  const [photos, setPhotos] = useState([])
  const [photoError, setPhotoError] = useState('')
  const [publishing, setPublishing] = useState(false)
  const photoPicker = useRef(null)
  const [topic,setTopic] = useState('Recientes')
  const [search, setSearch] = useState('')
  const [selectedPost, setSelectedPost] = useState(null)
  const topics = TOPICS
  const query = normalizeSearch(search.trim())
  const visiblePosts = posts.filter(post =>
    (!topics[topic] || topics[topic].test(post.content)) &&
    (!query || normalizeSearch(`${post.content} ${post.alias}`).includes(query))
  )

  async function load() {
    try {
      setPosts(await request('/community' + (moderation ? '/pending' : '')))
    } catch (error) {
      setMessage(error.message)
    }
  }

  useEffect(() => { load() }, [moderation])

  function selectPhotos(event) {
    const selected = Array.from(event.target.files)
    event.target.value = ''
    setPhotoError('')
    if (photos.length + selected.length > 2) {
      setPhotoError('Puedes adjuntar hasta dos fotos.')
      return
    }
    if (selected.some(file => !PHOTO_TYPES.includes(file.type) || file.size > MAX_PHOTO_BYTES || !file.size)) {
      setPhotoError('Selecciona fotos JPG, PNG o WebP de hasta 5 MB cada una.')
      return
    }
    setPhotos(previous => [...previous, ...selected])
  }

  async function publish(event) {
    event.preventDefault()
    if (publishing) return
    setPublishing(true)
    setMessage('')
    try {
      const encodedPhotos = await Promise.all(photos.map(encodePhoto))
      await request('/community', {
        method: 'POST',
        body: JSON.stringify({ alias, content, consent, photos: encodedPhotos }),
      })
      setContent('')
      setPhotos([])
      setPhotoError('')
      setConsent(false)
      setMessage('Publicación enviada a moderación.')
      setComposeOpen(false)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setPublishing(false)
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
          <div className="community-attachments">
            <div className="community-attachments__toolbar">
              <input ref={photoPicker} type="file" hidden multiple accept={PHOTO_TYPES.join(',')} onChange={selectPhotos} />
              <button
                className="community-attachments__picker"
                type="button"
                disabled={publishing || photos.length >= 2}
                onClick={() => photoPicker.current?.click()}
              >
                <span className="sa-icon" aria-hidden="true">add_photo_alternate</span>
                Agregar fotos
              </button>
              <small role="status">{photos.length} de 2 fotos</small>
            </div>
            <small>JPG, PNG o WebP de hasta 5 MB por foto. Oculta los datos personales antes de adjuntarlas.</small>
            {photoError && <small className="error" role="alert">{photoError}</small>}
            {photos.length > 0 && <ul aria-label="Fotos adjuntas">
              {photos.map((file, index) => <PhotoPreview
                key={`${index}-${file.name}-${file.lastModified}`}
                file={file}
                position={index + 1}
                disabled={publishing}
                onRemove={() => setPhotos(previous => previous.filter((_, item) => item !== index))}
              />)}
            </ul>}
          </div>
          <label>
            <input type="checkbox" required checked={consent}
              onChange={event => setConsent(event.target.checked)} />
            Autorizo publicar esta experiencia y he retirado los nombres y datos personales del texto y las fotos.
          </label>
          <button className="primary" disabled={publishing}>{publishing ? 'Enviando…' : 'Enviar para revisión'}</button>
        </form>
      )}
      {message && <p role="status">{message}</p>}
      <div id="community-posts" className="social-posts">
        {!moderation && <>
          <div className="community-search">
            <span className="sa-icon" aria-hidden="true">search</span>
            <input type="search" aria-label="Buscar experiencias" placeholder="Busca una empresa, app o experiencia…"
              value={search} onChange={event => setSearch(event.target.value)} />
          </div>
          <div className="social-filters" role="group" aria-label="Filtrar experiencias">
            {['Recientes', ...Object.keys(topics)].map(name => <button type="button" className={topic === name ? 'active' : ''}
              aria-pressed={topic === name} key={name} onClick={() => setTopic(name)}>{name}</button>)}
          </div>
          {posts.length > 0 && visiblePosts.length === 0 && <div className="community-search-empty" role="status">
            <p>No hay experiencias que coincidan con la búsqueda.</p>
            <button className="link-button" type="button" onClick={() => { setSearch(''); setTopic('Recientes') }}>Restablecer filtros</button>
          </div>}
        </>}
        {visiblePosts.map(post => (
        <article className="community-post" key={post.id}>
          <header className="social-post-header"><span className="social-avatar">{post.alias.slice(0,2).toUpperCase()}</span><div><b>{post.alias}</b><small>{new Date(post.created_at).toLocaleDateString('es-PE')} · Comunidad</small></div><span className="social-approved">{moderation?'Pendiente':'✓ Revisado por moderación'}</span></header>
          <p>{post.content}</p>
          {post.photos?.length > 0 && <div className="community-post-photos">
            {post.photos.map(position => <img
              key={position}
              src={communityPhotoUrl(post.id, position, moderation)}
              alt={`Foto ${position} adjunta a la publicación`}
              loading="lazy"
            />)}
          </div>}
          {!moderation && <div className="community-post__details">
            {post.photos?.length > 0 && <small>{post.photos.length} {post.photos.length === 1 ? 'foto adjunta' : 'fotos adjuntas'}</small>}
            <button type="button" className="link-button" onClick={() => setSelectedPost(post)}>Ver detalle →</button>
          </div>}
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
      {selectedPost && <PostDetail post={selectedPost} onClose={() => setSelectedPost(null)} />}
      {!posts.length && (
        <div className="community-empty"><h2>{moderation ? 'Todo al día' : 'Aquí comienzan las experiencias compartidas'}</h2><p>{moderation ? 'No hay publicaciones pendientes.' : 'Cuando se apruebe una publicación aparecerá en este muro.'}</p>{!moderation&&<button className="primary" onClick={()=>setComposeOpen(true)}>Comparte la primera experiencia</button>}</div>
      )}
      {moderation && <CommentModeration />}
    </section>
  )
}
