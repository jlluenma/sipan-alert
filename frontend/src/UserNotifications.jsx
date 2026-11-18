import { useEffect, useRef, useState } from 'react'
import { api, request } from './api'
import './user-notifications.css'

const statuses = {
  reports: { validado: 'Reporte validado', rechazado: 'Reporte rechazado' },
  posts: { publicado: 'Publicación aprobada', rechazado: 'Publicación rechazada' },
}

function readIds(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key))
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

export default function UserNotifications({ user, onLogin, onNavigate }) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(Boolean(user))
  const [error, setError] = useState(false)
  const key = `sipan-user-notifications-${user?.id}`
  const [read, setRead] = useState(() => user ? readIds(key) : [])
  const root = useRef(null)
  const bell = useRef(null)
  const sequence = useRef(0)
  const unread = items.filter(item => !read.includes(item.id)).length

  async function load() {
    const current = ++sequence.current
    setLoading(true)
    try {
      const [reports, posts] = await Promise.all([api.myReports(), request('/community/mine')])
      if (current !== sequence.current) return
      setItems([
        ...reports.map(report => ({
          target: 'reports', id: `report-${report.id}-${report.estado}`,
          title: statuses.reports[report.estado], detail: `Reporte #${report.id.slice(0, 8)}`,
          date: report.fecha,
        })),
        ...posts.map(post => ({
          target: 'posts', id: `post-${post.id}-${post.status}`,
          title: statuses.posts[post.status], detail: post.content, date: post.created_at,
        })),
      ].filter(item => item.title).sort((a, b) => new Date(b.date) - new Date(a.date)))
      setError(false)
    } catch {
      if (current === sequence.current) setError(true)
    } finally {
      if (current === sequence.current) setLoading(false)
    }
  }

  useEffect(() => {
    if (!user) return
    load()
    const timer = setInterval(load, 60_000)
    return () => {
      clearInterval(timer)
      sequence.current++
    }
  }, [user])

  useEffect(() => {
    if (!open) return
    function dismiss(event) {
      if (!root.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('pointerdown', dismiss)
    return () => document.removeEventListener('pointerdown', dismiss)
  }, [open])

  function markRead(ids) {
    const next = [...new Set([...read, ...ids])]
    setRead(next)
    try {
      localStorage.setItem(key, JSON.stringify(next))
    } catch {
      // Read state remains available for this session.
    }
  }

  return <div className="user-notifications" ref={root} onKeyDown={event => {
    if (event.key === 'Escape' && open) {
      setOpen(false)
      bell.current?.focus()
    }
  }}>
    <button type="button" className="user-notifications__bell" ref={bell}
      aria-label={unread ? `Notificaciones, ${unread} sin leer` : 'Notificaciones'}
      aria-expanded={open} onClick={() => {
        setOpen(!open)
        if (!open && user) load()
      }}>
      <span className="sa-icon" aria-hidden="true">notifications</span>
      {unread > 0 && <span className="notification-count" aria-hidden="true">{unread > 99 ? '99+' : unread}</span>}
    </button>
    {open && <section className="user-notifications__menu" aria-label="Notificaciones">
      <header>
        <strong>Notificaciones</strong>
        {unread > 0 && <button type="button" onClick={() => markRead(items.map(item => item.id))}>Marcar todas como leídas</button>}
      </header>
      {!user ? <>
        <p>Inicia sesión para ver el estado de tus aportes.</p>
        <button type="button" className="user-notifications__link" onClick={() => {
          setOpen(false)
          onLogin()
        }}>Iniciar sesión</button>
      </> : <>
        {error && <p role="status">No se pudieron cargar. <button type="button" className="user-notifications__link" onClick={load}>Reintentar</button></p>}
        {items.length ? <ul>{items.map(item => <li key={item.id}>
          <button type="button" className={read.includes(item.id) ? '' : 'unread'} onClick={() => {
            markRead([item.id])
            setOpen(false)
            onNavigate(item.target)
          }}>
            <strong>{item.title}</strong>
            <span>{item.detail}</span>
          </button>
        </li>)}</ul> : !error && <p role="status">{loading ? 'Cargando…' : 'Aquí aparecerán las decisiones sobre tus reportes y publicaciones.'}</p>}
      </>}
    </section>}
  </div>
}
