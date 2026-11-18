"""Publicaciones moderadas, separadas del dataset de aprendizaje."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sipan.persistence.database import session_scope
from sipan.preprocessing import anonymize

def community_router(current_user,reviewer):
    router=APIRouter(prefix='/api/community')
    class Publication(BaseModel):
        alias: str=Field(min_length=2,max_length=40)
        content: str=Field(min_length=20,max_length=1500)
        consent: bool
    class Decision(BaseModel):
        status: str
    class Comment(BaseModel):
        content: str=Field(min_length=3,max_length=800)
    @router.get('/mine')
    def mine(user=Depends(current_user)):
        with session_scope() as session:
            return [dict(row) for row in session.execute(text('SELECT id,alias,content,status,created_at FROM community_posts WHERE owner_id=:owner ORDER BY created_at DESC'),{'owner':UUID(user['id'])}).mappings()]
    @router.post('/{post_id}/withdraw')
    def withdraw(post_id:UUID,user=Depends(current_user)):
        with session_scope() as session:
            result=session.execute(text("UPDATE community_posts SET content='',status='retirado' WHERE id=:id AND owner_id=:owner"),{'id':post_id,'owner':UUID(user['id'])})
            if not result.rowcount:raise HTTPException(404,'Publicación no encontrada.')
        return {'status':'retirado'}
    @router.post('/{post_id}/edit')
    def edit(post_id:UUID,payload:Publication,user=Depends(current_user)):
        if not payload.consent:raise HTTPException(400,'Se requiere consentimiento.')
        with session_scope() as session:
            result=session.execute(text("UPDATE community_posts SET alias=:alias,content=:content,status='pendiente',reviewer_id=NULL WHERE id=:id AND owner_id=:owner AND status!='retirado'"),{'id':post_id,'owner':UUID(user['id']),'alias':anonymize(payload.alias).text,'content':anonymize(payload.content).text})
            if not result.rowcount:raise HTTPException(404,'Publicación no encontrada.')
        return {'status':'pendiente'}
    @router.get('/comments/pending')
    def pending_comments(user=Depends(reviewer)):
        with session_scope() as session:
            return [dict(row) for row in session.execute(text("SELECT id,post_id,content,created_at FROM community_comments WHERE status='pendiente' ORDER BY created_at")).mappings()]
    @router.post('/comments/{comment_id}/review')
    def review_comment(comment_id:UUID,payload:Decision,user=Depends(reviewer)):
        if payload.status not in {'publicado','rechazado'}:raise HTTPException(422,'Decisión inválida.')
        with session_scope() as session:
            result=session.execute(text("UPDATE community_comments SET status=:status WHERE id=:id AND status='pendiente'"),{'id':comment_id,'status':payload.status})
            if not result.rowcount:raise HTTPException(404,'Comentario no encontrado.')
        return {'status':payload.status}
    @router.get('/{post_id}/interactions')
    def interactions(post_id:UUID):
        with session_scope() as session:
            if not session.scalar(text("SELECT 1 FROM community_posts WHERE id=:id AND status='publicado'"),{'id':post_id}):raise HTTPException(404,'Publicación no disponible.')
            return {'useful':session.scalar(text('SELECT count(*) FROM community_reactions WHERE post_id=:id'),{'id':post_id}),'comments':[dict(row) for row in session.execute(text("SELECT id,content,created_at FROM community_comments WHERE post_id=:id AND status='publicado' ORDER BY created_at"),{'id':post_id}).mappings()]}
    @router.post('/{post_id}/comments',status_code=201)
    def comment(post_id:UUID,payload:Comment,user=Depends(current_user)):
        with session_scope() as session:
            if not session.scalar(text("SELECT 1 FROM community_posts WHERE id=:id AND status='publicado'"),{'id':post_id}):raise HTTPException(404,'Publicación no disponible.')
            session.execute(text('INSERT INTO community_comments(post_id,owner_id,content) VALUES (:id,:owner,:content)'),{'id':post_id,'owner':UUID(user['id']),'content':anonymize(payload.content).text})
        return {'status':'pendiente'}
    @router.post('/{post_id}/useful')
    def useful(post_id:UUID,user=Depends(current_user)):
        with session_scope() as session:
            if not session.scalar(text("SELECT 1 FROM community_posts WHERE id=:id AND status='publicado'"),{'id':post_id}):raise HTTPException(404,'Publicación no disponible.')
            session.execute(text('INSERT INTO community_reactions(post_id,owner_id) VALUES (:id,:owner) ON CONFLICT DO NOTHING'),{'id':post_id,'owner':UUID(user['id'])})
        return {'status':'registrado'}
    @router.get('')
    def feed():
        with session_scope() as session:
            return [dict(row) for row in session.execute(text("SELECT id,alias,content,created_at FROM community_posts WHERE status='publicado' ORDER BY created_at DESC LIMIT 100")).mappings()]
    @router.post('',status_code=201)
    def publish(payload:Publication,user=Depends(current_user)):
        if not payload.consent: raise HTTPException(400,'Autoriza la publicación antes de enviarla.')
        with session_scope() as session:
            session.execute(text("INSERT INTO community_posts(owner_id,alias,content) VALUES (:owner,:alias,:content)"),{'owner':UUID(user['id']),'alias':anonymize(payload.alias).text,'content':anonymize(payload.content).text})
        return {'status':'pendiente'}
    @router.get('/pending')
    def pending(user=Depends(reviewer)):
        with session_scope() as session:
            return [dict(row) for row in session.execute(text("SELECT id,alias,content,created_at FROM community_posts WHERE status='pendiente' ORDER BY created_at")).mappings()]
    @router.post('/{post_id}/review')
    def review(post_id:UUID,payload:Decision,user=Depends(reviewer)):
        if payload.status not in {'publicado','rechazado'}:raise HTTPException(422,'Decisión inválida.')
        with session_scope() as session:
            result=session.execute(text("UPDATE community_posts SET status=:status,reviewer_id=:reviewer WHERE id=:id AND status='pendiente'"),{'id':post_id,'status':payload.status,'reviewer':UUID(user['id'])})
            if not result.rowcount:raise HTTPException(404,'La publicación no está pendiente.')
        return {'status':payload.status}
    return router
