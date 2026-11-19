import { jsPDF } from 'jspdf'

export function createResultPdf({ result, summary, shared, context, situation, source }) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const left = 19
  const width = 172
  let y = 22

  function write(value, size = 11, bold = false) {
    doc.setFont('helvetica', bold ? 'bold' : 'normal')
    doc.setFontSize(size)
    doc.setTextColor('#253041')
    const lines = doc.splitTextToSize(value, width)
    for (const line of lines) {
      if (y > 268) {
        doc.addPage()
        y = 23
      }
      doc.text(line, left, y)
      y += size * 0.45
    }
    y += 2
  }

  doc.setProperties({ title: 'Ficha del análisis de oferta', author: 'SipánAlert' })
  doc.setFillColor('#a8181e')
  doc.rect(0, 0, 210, 5, 'F')
  write('SipánAlert', 12, true)
  write('Ficha del análisis de oferta', 22, true)
  const date = new Intl.DateTimeFormat('es-PE', { dateStyle: 'long', timeZone: 'America/Lima' }).format(new Date())
  write(date, 10)
  write('Resumen orientativo de señales de riesgo.', 10)

  y += 4
  write('Señales del análisis', 15, true)
  const signals = [...result.signals, ...result.possibleSignals]
  if (!signals.length) write('El análisis no identificó señales. Verifica la oferta por un canal oficial.')
  for (const signal of signals) {
    const prefix = result.possibleSignals.includes(signal) ? 'Posible: ' : ''
    write(`${prefix}${signal.title}`, 11, true)
    write(signal.explanation)
  }

  y += 3
  write('Reportes parecidos', 15, true)
  write(summary)
  if (shared.length) write(`Señales frecuentes: ${shared.join(', ')}.`)
  if (context) write(context)

  y += 3
  write('¿Qué hago ahora?', 15, true)
  if (situation) {
    write(situation.title, 11, true)
    situation.steps.forEach((step, index) => write(`${index + 1}. ${step}`))
  } else {
    write('Verifica la oferta por un canal oficial antes de enviar dinero o datos.')
  }

  if (y > 262) {
    doc.addPage()
    y = 23
  }
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor('#a8181e')
  doc.textWithLink('Canales oficiales y orientación de la SBS', left, y + 4, { url: source })
  const pages = doc.getNumberOfPages()
  for (let page = 1; page <= pages; page++) {
    doc.setPage(page)
    doc.setFontSize(9)
    doc.setTextColor('#566173')
    doc.text(`SipánAlert  |  ${page} de ${pages}`, left, 285)
  }
  return doc
}
