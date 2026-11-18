import {useEffect,useState} from 'react'
import {request} from './api'
export function Interactions({id}){
 const [data,setData]=useState({useful:0,comments:[]}),[content,setContent]=useState(''),[message,setMessage]=useState('')
 async function load(){try{setData(await request(`/community/${id}/interactions`))}catch(e){setMessage(e.message)}}
 useEffect(()=>{load()},[id])
 return <div><button className="secondary" onClick={async()=>{try{await request(`/community/${id}/useful`,{method:'POST'});load()}catch(e){setMessage(e.message)}}}>Me resultó útil · {data.useful}</button>{data.comments.map(c=><p key={c.id}>{c.content}</p>)}<form onSubmit={async e=>{e.preventDefault();try{await request(`/community/${id}/comments`,{method:'POST',body:JSON.stringify({content})});setContent('');setMessage('Comentario enviado a moderación.')}catch(err){setMessage(err.message)}}}><label>Comentario<input required minLength={3} maxLength={800} value={content} onChange={e=>setContent(e.target.value)}/></label><button>Enviar comentario</button></form>{message&&<p role="status">{message}</p>}</div>
}
export function OwnPublications(){
 const [rows,setRows]=useState([]),[message,setMessage]=useState('')
 async function load(){try{setRows(await request('/community/mine'))}catch(e){setMessage(e.message)}}
 return <details><summary onClick={load}>Mis publicaciones</summary>{message&&<p>{message}</p>}{rows.map(row=><article className="community-post" key={row.id}><b>{row.alias} · {row.status}</b><p>{row.content}</p>{row.status!=='retirado'&&<button className="secondary" onClick={async()=>{try{await request(`/community/${row.id}/withdraw`,{method:'POST'});load()}catch(e){setMessage(e.message)}}}>Retirar publicación</button>}</article>)}</details>
}
export function CommentModeration(){
 const [rows,setRows]=useState([]),[error,setError]=useState('')
 async function load(){try{setRows(await request('/community/comments/pending'))}catch(e){setError(e.message)}}
 useEffect(()=>{load()},[])
 return <section><h2>Comentarios pendientes</h2>{error&&<p>{error}</p>}{rows.map(row=><article className="community-post" key={row.id}><p>{row.content}</p>{['publicado','rechazado'].map(status=><button className="secondary" key={status} onClick={async()=>{try{await request(`/community/comments/${row.id}/review`,{method:'POST',body:JSON.stringify({status})});load()}catch(e){setError(e.message)}}}>{status==='publicado'?'Aprobar':'Rechazar'}</button>)}</article>)}</section>
}
