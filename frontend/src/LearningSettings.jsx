import { useState } from 'react'

export default function LearningSettings() {
  const defaults={similarity:35,evaluation:20,minimum:2}
  const [values,setValues]=useState(defaults),[saved,setSaved]=useState(false)
  function change(key,value){setValues({...values,[key]:Number(value)});setSaved(false)}
  return <section className="module-card settings-form"><h2>Configuración del aprendizaje</h2><p>Ajusta una propuesta de configuración antes de aplicarla al sistema.</p>
    <form onSubmit={event=>{event.preventDefault();setSaved(true)}}>
      <fieldset><legend>Patrones candidatos</legend><label>Similitud mínima: {values.similarity}%<input type="range" min="10" max="95" value={values.similarity} onChange={e=>change('similarity',e.target.value)}/></label><label>Mensajes mínimos por grupo<input type="number" min="2" max="100" required value={values.minimum} onChange={e=>change('minimum',e.target.value)}/></label></fieldset>
      <fieldset><legend>Dataset evolutivo</legend><label>Porcentaje reservado para evaluación<input type="number" min="10" max="40" required value={values.evaluation} onChange={e=>change('evaluation',e.target.value)}/></label><p>Entrenamiento: {100-values.evaluation}% · Evaluación: {values.evaluation}%</p><p>Los grupos similares deben permanecer en una misma partición.</p></fieldset>
      <fieldset><legend>Control humano y modelos</legend><label><input type="checkbox" checked disabled/> Revisión humana obligatoria</label><label><input type="checkbox" checked disabled/> Excluir reportes pendientes, rechazados y duplicados</label><label><input type="checkbox" checked={false} disabled/> Reentrenamiento automático</label><p>Modelo actual: TF-IDF + regresión logística. Los umbrales se revisan mediante evaluación.</p></fieldset>
      <div className="settings-actions"><button className="primary">Guardar propuesta de demostración</button><button type="button" className="secondary" onClick={()=>{setValues(defaults);setSaved(false)}}>Restablecer</button></div>
      {saved&&<p role="status" className="module-feedback">Propuesta guardada durante esta sesión de demostración. Todavía no modifica la API ni el modelo.</p>}
    </form></section>
}
