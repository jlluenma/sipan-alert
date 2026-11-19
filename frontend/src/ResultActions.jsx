import { useState } from 'react'
import './result-actions.css'

const SBS_GUIDE = 'https://www.sbs.gob.pe/usuarios/aprende-con-la-sbs/denuncia-la-informalidad'
const SIGNAL_NAMES = {
  pago_anticipado: 'Pago por adelantado',
  acceso_invasivo: 'Acceso invasivo',
  amenaza_presion: 'Amenaza o presión',
  condiciones_opacas: 'Condiciones ocultas',
}

const situations = [
  {
    title: 'Solo recibí el mensaje',
    steps: [
      'Evita pagar, abrir enlaces o compartir datos mientras verificas la oferta.',
      'Busca la entidad por tu cuenta y verifica por un canal oficial si reconoce la oferta.',
      'Conserva el mensaje si quieres reportar la oferta.',
    ],
  },
  {
    title: 'Ya compartí mis datos',
    steps: [
      'Si compartiste claves o códigos, cambia las contraseñas afectadas desde el canal oficial y cierra las sesiones abiertas.',
      'Si compartiste información bancaria, contacta a tu entidad por un canal oficial para proteger tus cuentas.',
      'Si instalaste una app de préstamo, revisa y revoca permisos como acceso a contactos o fotos.',
    ],
  },
  {
    title: 'Ya envié dinero',
    steps: [
      'Contacta cuanto antes a tu banco o billetera digital por su canal oficial. Reporta el pago y pide un número de caso.',
      'Guarda el comprobante, las capturas y la conversación original. Evita enviar dinero adicional.',
      'Si sospechas una estafa, usa los canales oficiales de la Policía Nacional o del Ministerio Público.',
    ],
  },
]

function describeMatches(matches) {
  if (!matches) return 'La comparación con reportes revisados no estuvo disponible.'
  if (!matches.count) return 'Aún no hay suficientes coincidencias en los reportes revisados.'
  return `Encontramos ${matches.count} reportes revisados con texto parecido.`
}

export default function ResultActions({ result }) {
  const [selected, setSelected] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState('')
  const situation = situations[selected]
  const matches = result.similarReports
  const summary = describeMatches(matches)
  const shared = (matches?.labels || []).map(label => SIGNAL_NAMES[label]).filter(Boolean)
  const context = matches?.count ? 'La similitud ayuda a orientar la revisión de la oferta.' : ''

  async function download() {
    setDownloading(true)
    setDownloadError('')
    try {
      const { createResultPdf } = await import('./resultPdf')
      const pdf = createResultPdf({ result, summary, shared, context, situation, source: SBS_GUIDE })
      pdf.save('ficha-sipanalert.pdf')
    } catch {
      setDownloadError('No se pudo generar la ficha. Inténtalo de nuevo.')
    } finally {
      setDownloading(false)
    }
  }

  return <>
    <section className="result-action-card">
      <h2>¿Alguien más recibió una oferta parecida?</h2>
      <p>{summary}</p>
      {shared.length > 0 && <ul className="result-match-labels" aria-label="Señales frecuentes en los reportes parecidos">
        {shared.map(label => <li key={label}>{label}</li>)}
      </ul>}
      {context && <small>{context}</small>}
    </section>
    <section className="result-action-card">
      <h2>¿Qué hago ahora?</h2>
      <div className="result-situations" role="group" aria-label="Elige qué pasó con la oferta">
        {situations.map(({ title }, index) => <button key={title} type="button"
          aria-pressed={selected === index} onClick={() => setSelected(index)}>{title}</button>)}
      </div>
      <div aria-live="polite">
        {situation ? <ol>
          {situation.steps.map(step => <li key={step}>{step}</li>)}
        </ol> : <p>Elige tu situación para ver los pasos recomendados.</p>}
      </div>
      <a href={SBS_GUIDE} target="_blank" rel="noreferrer">Canales oficiales de la SBS</a>
    </section>
    <section className="result-action-card result-download">
      <div>
        <h2>Ficha del análisis</h2>
        <p>Guarda las señales, las coincidencias y los pasos de la situación que elijas.</p>
      </div>
      <button className="primary" type="button" disabled={downloading} onClick={download}>
        {downloading ? 'Generando…' : 'Descargar PDF'}
      </button>
      {downloadError && <p className="error" role="alert">{downloadError}</p>}
    </section>
  </>
}
