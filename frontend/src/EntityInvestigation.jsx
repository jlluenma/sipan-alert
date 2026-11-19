import { useEffect, useState } from 'react'
import ChatText from './ChatText'
import { request } from './api'
import './entity-investigation.css'

const REGISTER = 'https://www.sbs.gob.pe/supervisados-y-registros/registros/otros-registros/casas-de-cambio-prestamos-y-empenos/publicacion-del-registro'
const dateFormat = new Intl.DateTimeFormat('es-PE', { dateStyle: 'long', timeZone: 'America/Lima' })
const formatDate = date => dateFormat.format(new Date(date.length === 10 ? `${date}T12:00:00-05:00` : date))
const identifierNames = { package: 'Identificador de Android', domain: 'Dominio publicado' }
const views = [
  ['summary', 'Resumen', 'description'],
  ['identifiers', 'Identificadores', 'fingerprint'],
  ['relations', 'Relaciones', 'hub'],
  ['community', 'Reportes', 'forum'],
  ['evidence', 'Evidencias', 'fact_check'],
  ['activity', 'Actividad', 'event_note'],
  ['news', 'Noticias', 'newspaper'],
]

const categories = [
  ['all', 'Todos', 'search'],
  ['app', 'Aplicaciones', 'smartphone'],
  ['company', 'Empresas', 'business'],
  ['domain', 'Dominios', 'language'],
]

function matchesCategory(entity, category) {
  if (category === 'app') return entity.kind === 'aplicación'
  if (category === 'company') return entity.kind === 'empresa'
  if (category === 'domain') return Boolean(entity.identifiers.domain)
  return true
}

function Results({ found, query, onSelect }) {
  return <>
    <p role="status">{found.length
      ? `${found.length} ${found.length === 1 ? 'coincidencia' : 'coincidencias'} para «${query}».`
      : `Sin coincidencias para «${query}» en el catálogo consultado.`}</p>
    {found.length > 0 && <ul className="investigation__results">
      {found.map((entity, index) => <li className="investigation__card investigation__result" key={entity.name}>
        <div>
          <span className="investigation__kind">{entity.kind}</span>
          <h2>{entity.name}</h2>
          <p>{entity.match === 'identificador' ? 'Coincidencia por identificador' : 'Coincidencia por nombre'}</p>
          <small>{entity.alerts.length} {entity.alerts.length === 1 ? 'comunicado oficial' : 'comunicados oficiales'}</small>
        </div>
        <button type="button" className="primary" onClick={() => onSelect(index)}>Ver perfil de entidad →</button>
      </li>)}
    </ul>}
  </>
}

function Summary({ entity, onView }) {
  const metrics = [
    ['Evidencias del proveedor', entity.publisherEvidence?.length ?? 0, 'evidence'],
    ['Identificadores', Object.keys(entity.identifiers).length, 'identifiers'],
    ['Entidades relacionadas', entity.relations.length, 'relations'],
    ['Menciones comunitarias', entity.community?.length ?? '—', 'community'],
  ]
  return <section className="investigation__card">
    <h2>Resumen de investigación</h2>
    <p>{entity.match === 'nombre' ? 'Si la oferta usa este nombre, contrasta su identidad con los datos del catálogo.' : 'El identificador consultado aparece en los comunicados enlazados.'}
      {' '}Puedes revisar los materiales publicados por el proveedor y los comunicados fechados en la ficha.</p>
    <div className="investigation__metrics">
      {metrics.map(([label, count, destination]) => <button key={destination} type="button" onClick={() => onView(destination)}>
        <strong>{count}</strong><span>{label} →</span>
      </button>)}
    </div>
  </section>
}

function Identifiers({ entity }) {
  return <section className="investigation__card">
    <h2>Identificadores de la entidad</h2>
    {!Object.keys(entity.identifiers).length && !entity.aliases.length && <p>Las fuentes consultadas solo identifican esta entidad por su nombre.</p>}
    <dl className="investigation__identifiers">
      {Object.entries(entity.identifiers).map(([type, value]) => <div key={type}>
        <dt>{identifierNames[type]}</dt><dd><code>{value}</code></dd>
      </div>)}
      {entity.aliases.length > 0 && <div><dt>Nombres asociados en el catálogo</dt><dd>{entity.aliases.join(', ')}</dd></div>}
    </dl>
    <h3>Fuentes del catálogo</h3>
    <ul>{entity.alerts.map(alert => <li key={alert.url}>
      <a href={alert.url} target="_blank" rel="noreferrer">SBS · {formatDate(alert.date)} ↗</a>
    </li>)}</ul>
  </section>
}

function Activity({ entity, onView }) {
  const entries = [
    ...entity.alerts.map(alert => ({ date: alert.date, title: alert.title })),
    ...(entity.community || []).map(post => ({ date: post.date, title: 'Mención publicada en Comunidad', view: 'community' })),
  ].sort((first, second) => second.date.localeCompare(first.date))
  return <section className="investigation__card">
    <h2>Actividad documentada</h2>
    <ol className="investigation__activity">{entries.map(({ date, title, view }, index) => <li key={`${date}-${index}`}>
      <time dateTime={date}>{formatDate(date)}</time>
      {view ? <button type="button" className="link-button" onClick={() => onView(view)}>{title} →</button> : <span>{title}</span>}
    </li>)}</ol>
    <h3>Comunicados de la SBS</h3>
    <Sources alerts={entity.alerts} />
  </section>
}

function PublisherEvidence({ entity }) {
  const evidence = entity.publisherEvidence || []
  return <section className="investigation__card">
    <h2>Evidencias de la entidad</h2>
    {!evidence.length && <p>Todavía no hay materiales del proveedor verificables en este catálogo.</p>}
    {evidence.map(item => <article className="investigation__source-preview" key={item.url}>
      <h3>{item.title}</h3>
      <small>{item.source} · Actualizada el {formatDate(item.updatedAt)}</small>
      <p><strong>Desarrollador que figura en la tienda:</strong> {item.publisher}.</p>
      {item.title !== entity.name && <p>Esta ficha se encontró por el identificador compartido <code>{entity.identifiers.package || entity.identifiers.domain}</code>. En la tienda aparece con el nombre <strong>{item.title}</strong>.</p>}
      <p>{item.description}</p>
      <dl className="investigation__identifiers">{item.terms.map(term => <div key={term.label}>
        <dt>{term.label}</dt><dd>{term.value}</dd>
      </div>)}</dl>
      <p><strong>Ejemplo publicado.</strong> {item.example}</p>
      <p><strong>Datos personales.</strong> {item.dataDisclosure}</p>
      <small>Los datos y condiciones corresponden a lo que declara el proveedor en su ficha pública.</small>
      <a href={item.url} target="_blank" rel="noreferrer">Consultar ficha del desarrollador ↗</a>
    </article>)}
  </section>
}

function EvidenceRecords({ records, grouped = false }) {
  return <div className="investigation__evidence-table" role="region" aria-label="Datos registrados en la fuente" tabIndex={0}>
    <table>
      <thead><tr><th scope="col">Nombre publicado</th><th scope="col">Datos citados</th>{grouped && <th scope="col">Comunicado</th>}</tr></thead>
      <tbody>{records.map((source, index) => <tr key={`${source.url}-${source.record.name}-${index}`}>
        <th scope="row">{source.record.name}</th>
        <td>
          {source.record.aliases.length > 0 && <div>Otros nombres: {source.record.aliases.join(', ')}</div>}
          {Object.entries(source.record.identifiers).map(([kind, value]) => <div key={kind}>
            <span>{identifierNames[kind]}</span><code>{value}</code>
          </div>)}
          {!source.record.aliases.length && !Object.keys(source.record.identifiers).length && 'Mención por nombre'}
        </td>
        {grouped && <td><a href={source.url} target="_blank" rel="noreferrer">SBS · {formatDate(source.date)} ↗</a></td>}
      </tr>)}</tbody>
    </table>
  </div>
}

function Sources({ alerts }) {
  const dates = [...alerts].sort((a, b) => a.date.localeCompare(b.date))
  const [selected, setSelected] = useState(dates[0].url)
  const active = dates.find(alert => alert.url === selected) || dates[0]
  return <>
    <ol className="investigation__timeline" aria-label="Cronología de comunicados">
      {dates.map(alert => <li key={alert.url}>
        <button type="button" aria-pressed={active.url === alert.url} onClick={() => setSelected(alert.url)}>
          <time dateTime={alert.date}>{formatDate(alert.date)}</time>
        </button>
      </li>)}
    </ol>
    <div className="investigation__source-preview" aria-live="polite">
      <h3>Ficha de evidencia</h3>
      <strong>{active.title}</strong>
      <small>SBS · Comunicado oficial · {formatDate(active.date)}</small>
      {active.context && <p>{active.context}</p>}
      {active.record && <EvidenceRecords records={[active]} />}
      <p><strong>Alcance.</strong> El registro documenta la mención de la entidad en esa fecha. La identidad del remitente de una oferta se verifica por separado.</p>
      {active.reviewedAt && <small>Revisión del catálogo: {formatDate(active.reviewedAt)}</small>}
      <a href={active.url} target="_blank" rel="noreferrer">Consultar comunicado original ↗</a>
    </div>
  </>
}

function EntityRelationshipMap({ entity, onExplore, busy }) {
  const [selected, setSelected] = useState(0)
  const relation = entity.relations[selected]
  const evidence = relation
    ? [...(relation.originSources || []), ...relation.sources].filter(source => source.record)
    : []
  if (!relation) return <p>El catálogo consultado no muestra identificadores compartidos.</p>

  return <>
    <div className="investigation__map-layout">
      <div className="investigation__map" role="group" aria-label="Mapa de relaciones por identificador compartido">
        <strong className="investigation__map-origin">{entity.name}</strong>
        <ul aria-label="Entidades relacionadas">
          {entity.relations.map((item, index) => <li key={`${item.name}-${item.kind}`}>
            <button type="button" aria-pressed={selected === index} onClick={() => setSelected(index)}>
              <span className="sa-icon" aria-hidden="true">hub</span>
              {item.name}
            </button>
          </li>)}
        </ul>
      </div>
      <div className="investigation__map-evidence" aria-live="polite">
        <h3>{relation.name}</h3>
        <p><strong>Coincidencia documentada</strong></p>
        <p>Las dos fichas aparecen en fuentes de la SBS con el mismo {identifierNames[relation.kind].toLowerCase()}.</p>
        <code>{relation.value}</code>
        <p><small>El identificador de Android es el código que distingue el paquete de una aplicación. La coincidencia corresponde al código publicado.</small></p>
        <button className="link-button" type="button" onClick={() => onExplore(relation.name)} disabled={busy}>
          Explorar {relation.name} →
        </button>
      </div>
    </div>
    <section className="investigation__source-preview">
      <h3>Evidencia del vínculo</h3>
      {evidence.length > 0 && <EvidenceRecords records={evidence} grouped />}
      <p><strong>Alcance.</strong> La relación refleja el identificador citado para ambos nombres. La titularidad, un posible cambio de nombre o la autenticidad de una oferta requieren una verificación adicional.</p>
    </section>
  </>
}

export default function EntityInvestigation({ user, onLogin, onCommunity, onAnalyze }) {
  const [query, setQuery] = useState('')
  const [searched, setSearched] = useState('')
  const [entities, setEntities] = useState([])
  const [screen, setScreen] = useState('search')
  const [category, setCategory] = useState('all')
  const [profilePath, setProfilePath] = useState([])
  const [recent, setRecent] = useState([])
  const [news, setNews] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [view, setView] = useState('summary')
  const entity = profilePath.at(-1)
  const featuredAlert = entity?.alerts.at(-1)
  const found = entities.filter(item => matchesCategory(item, category))

  useEffect(() => {
    if (screen !== 'search') window.scrollTo(0, 0)
  }, [screen, entity])

  async function search(event) {
    event.preventDefault()
    await runSearch(query)
  }

  async function runSearch(input) {
    const value = input.trim()
    if (busy || value.length < 3) return
    setQuery(value)
    setBusy('catalog')
    setError('')
    setNews(null)
    try {
      const result = await request('/investigation', { method: 'POST', body: JSON.stringify({ query: value }) })
      setEntities(result.entities)
      setSearched(value)
      setRecent(previous => [value, ...previous.filter(item => item !== value)].slice(0, 4))
      setProfilePath([])
      setScreen('results')
    } catch {
      setError('No se pudo consultar el catálogo. Inténtalo de nuevo.')
    } finally {
      setBusy('')
    }
  }

  function openProfile(item) {
    setProfilePath([item])
    setView('summary')
    setNews(null)
    setError('')
    setScreen('profile')
  }

  async function exploreRelated(name) {
    setBusy('catalog')
    setError('')
    try {
      const result = await request('/investigation', { method: 'POST', body: JSON.stringify({ query: name }) })
      const related = result.entities.find(item => item.name === name)
      if (!related) throw new Error()
      setProfilePath(previous => [...previous, related])
      setView('relations')
      setNews(null)
    } catch {
      setError('No se pudo abrir la ficha relacionada. Inténtalo de nuevo.')
    } finally {
      setBusy('')
    }
  }

  function backToResults() {
    setProfilePath([])
    setQuery(searched)
    setNews(null)
    setError('')
    setScreen('results')
  }

  async function loadNews() {
    if (!user) return onLogin()
    setBusy('news')
    setNews(null)
    try {
      const name = entity?.name || searched
      const identifier = entity?.identifiers.package || entity?.identifiers.domain
      setNews(await request('/investigation/news', {
        method: 'POST', body: JSON.stringify({ query: [name, identifier].filter(Boolean).join(' ').slice(0, 120) }),
      }))
    } catch {
      setNews({ message: 'No se pudo consultar noticias. Inténtalo de nuevo.', sources: [] })
    } finally {
      setBusy('')
    }
  }

  return <main className="page investigation">
    {screen === 'search' && <>
      <h1>Investigar entidad</h1>
      <p className="muted">Busca una aplicación o empresa de préstamos por nombre, dominio o identificador de Android.</p>
    </>}
    {screen === 'results' && <>
      <button type="button" className="link-button" disabled={Boolean(busy)} onClick={() => {
        setQuery('')
        setCategory('all')
        setNews(null)
        setError('')
        setScreen('search')
      }}>← Volver al buscador</button>
      <h1>Resultados de búsqueda</h1>
    </>}
    {screen !== 'profile' && <form className="investigation__search" onSubmit={search}>
      <label htmlFor="entity-query">Nombre o identificador</label>
      <input id="entity-query" value={query} onChange={event => setQuery(event.target.value)}
        required minLength={3} maxLength={120} placeholder="Ejemplo: Sol Dinero" />
      <button className="primary" disabled={Boolean(busy) || query.trim().length < 3}>
        {busy === 'catalog' ? 'Buscando…' : 'Buscar'}
      </button>
    </form>}
    {screen !== 'profile' && <div className="investigation__views" role="group" aria-label="Tipo de búsqueda">
      {categories.map(([value, label, icon]) => <button key={value} type="button" aria-pressed={category === value}
        onClick={() => setCategory(value)}><span className="sa-icon" aria-hidden="true">{icon}</span>{label}</button>)}
    </div>}
    {screen === 'search' && <section className="investigation__card">
      <h2>{recent.length ? 'Consultas de esta visita' : 'Prueba una búsqueda'}</h2>
      <div className="investigation__examples">
        {(recent.length ? recent : ['Sol Dinero', 'Moni Amigo']).map(item => <button key={item} type="button" disabled={Boolean(busy)}
          onClick={() => { setCategory('all'); runSearch(item) }}>{item}</button>)}
      </div>
    </section>}
    {error && <p className="error" role="alert">{error}</p>}
    {screen === 'results' && <Results found={found} query={searched} onSelect={index => openProfile(found[index])} />}
    {screen === 'profile' && entity && <>
        <div className="investigation__back">
          <button type="button" className="link-button" disabled={Boolean(busy)} onClick={backToResults}>← Volver a resultados</button>
          {profilePath.length > 1 && <button type="button" className="link-button" disabled={Boolean(busy)} onClick={() => {
            setProfilePath(previous => previous.slice(0, -1))
            setView('relations')
            setNews(null)
            setError('')
          }}>Volver a {profilePath.at(-2).name}</button>}
        </div>
        <section className="investigation__card investigation__profile">
          <small>{entity.kind}</small>
          <h1>{entity.name}</h1>
          <p><strong>{entity.match === 'identificador' ? 'Coincidencia por identificador' : 'Coincidencia por nombre'}</strong></p>
        </section>
        {featuredAlert && <aside className="investigation__alert" aria-labelledby="investigation-alert-heading">
          <span className="sa-icon" aria-hidden="true">warning</span>
          <div>
            <h2 id="investigation-alert-heading">Advertencia de la SBS</h2>
            <p><time dateTime={featuredAlert.date}>{formatDate(featuredAlert.date)}</time> · {featuredAlert.title}</p>
            {featuredAlert.recommendation && <p><strong>{featuredAlert.recommendation}</strong></p>}
            <a href={featuredAlert.url} target="_blank" rel="noreferrer">Ver comunicado oficial ↗</a>
          </div>
        </aside>}
        <div className="investigation__views" role="group" aria-label="Explorar la ficha">
          {views.map(([value, label, icon]) => <button key={value} type="button" aria-pressed={view === value}
            onClick={() => setView(value)}>
            <span className="sa-icon" aria-hidden="true">{icon}</span>{label}
            {value === 'evidence' && <span className="investigation__count">{entity.publisherEvidence?.length ?? 0}</span>}
            {value === 'relations' && <span className="investigation__count">{entity.relations.length}</span>}
          </button>)}
        </div>
        {view === 'summary' && <Summary entity={entity} onView={setView} />}
        {view === 'identifiers' && <Identifiers entity={entity} />}
        {view === 'activity' && <Activity entity={entity} onView={setView} />}
        {view === 'evidence' && <PublisherEvidence entity={entity} />}
        {view === 'relations' && <section className="investigation__card">
          <h2>Mapa de relaciones</h2>
          <EntityRelationshipMap key={entity.name} entity={entity} busy={Boolean(busy)} onExplore={exploreRelated} />
        </section>}
        {view === 'community' && <section className="investigation__card">
          <h2>Menciones en Comunidad</h2>
          {entity.community?.length ? <>
            <p>Experiencias publicadas tras moderación. Las coincidencias se basan en el nombre mencionado.</p>
            <ul className="investigation__mentions">{entity.community.map((post, index) => <li key={index}>
              <time dateTime={post.date}>{formatDate(post.date)}</time>
              <p>{post.excerpt}</p>
            </li>)}</ul>
          </> : <p>{entity.community ? 'No hay coincidencias en las publicaciones recientes consultadas.' : 'Comunidad no estuvo disponible para esta consulta.'}</p>}
          <button type="button" className="link-button" onClick={onCommunity}>Ir a Comunidad</button>
        </section>}
    </>}
    {(screen === 'profile' && view === 'news' || screen === 'results' && !found.length) && <section className="investigation__card">
        <h2>Noticias y otras fuentes</h2>
        <p>Busca publicaciones relacionadas y revisa las fuentes originales.</p>
        <button type="button" className="secondary" disabled={Boolean(busy)} onClick={loadNews}>
          {busy === 'news' ? 'Consultando…' : user ? 'Buscar noticias' : 'Iniciar sesión para buscar noticias'}
        </button>
        {news && <div className="investigation__news" aria-live="polite">
          <ChatText text={news.message} />
          {news.sources.length > 0 && <ul>{news.sources.map((source, index) => <li key={index}>
            <a href={source.url} target="_blank" rel="noreferrer">{source.name}</a>
          </li>)}</ul>}
        </div>}
    </section>}
    {screen !== 'search' && <section className="investigation__card">
        <h2>Qué puedes hacer</h2>
        <p>{entity ? 'Si recibiste una oferta con este nombre, contrasta el identificador y consulta la fuente original antes de instalar la app o compartir datos.' : 'Si tienes una oferta, contrasta el nombre o RUC con fuentes oficiales y consulta las señales del mensaje.'}</p>
        <div className="investigation__actions">
          <button type="button" className="primary" onClick={onAnalyze}>Analizar una oferta</button>
          <a href={REGISTER} target="_blank" rel="noreferrer">Consultar el registro SBS</a>
        </div>
    </section>}
  </main>
}
