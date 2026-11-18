"""Publicaciones moderadas, separadas del dataset de aprendizaje."""
from base64 import b64decode
from binascii import Error as Base64Error
from io import BytesIO
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from sqlalchemy import text
from sipan.persistence.database import session_scope
from sipan.preprocessing import anonymize

MAX_PHOTO_BYTES = 5 * 1024 * 1024
EncodedPhoto = Annotated[str, Field(max_length=4 * ((MAX_PHOTO_BYTES + 2) // 3))]
POST_FIELDS = """id, alias, content, created_at,
    ARRAY(SELECT position FROM community_post_photos
          WHERE post_id=community_posts.id ORDER BY position) AS photos"""


def normalize_photo(encoded):
    try:
        raw = b64decode(encoded, validate=True)
        if len(raw) > MAX_PHOTO_BYTES:
            raise ValueError('Tamaño de archivo inválido')
        with Image.open(BytesIO(raw), formats=['JPEG', 'PNG', 'WEBP']) as source:
            if source.width * source.height > 25_000_000:
                raise ValueError('Dimensiones inválidas')
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((1800, 1800))
            image.info.clear()
            output = BytesIO()
            image.save(output, format='JPEG', quality=86)
            return output.getvalue()
    except (Base64Error, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'Usa fotos JPG, PNG o WebP válidas de hasta 5 MB y 25 megapíxeles.')


def community_router(current_user,reviewer):
    router=APIRouter(prefix='/api/community')
    class Publication(BaseModel):
        alias: str=Field(min_length=2,max_length=40)
        content: str=Field(min_length=20,max_length=1500)
        consent: bool
    class NewPublication(Publication):
        photos: list[EncodedPhoto] = Field(default_factory=list, max_length=2)
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
            session.execute(text('DELETE FROM community_post_photos WHERE post_id=:id'), {'id': post_id})
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
            return [dict(row) for row in session.execute(text(f"SELECT {POST_FIELDS} FROM community_posts WHERE status='publicado' ORDER BY created_at DESC LIMIT 100")).mappings()]
    @router.post('',status_code=201)
    def publish(payload:NewPublication,user=Depends(current_user)):
        if not payload.consent: raise HTTPException(400,'Autoriza la publicación antes de enviarla.')
        photos = [normalize_photo(photo) for photo in payload.photos]
        with session_scope() as session:
            post_id = session.scalar(text("INSERT INTO community_posts(owner_id,alias,content) VALUES (:owner,:alias,:content) RETURNING id"),{'owner':UUID(user['id']),'alias':anonymize(payload.alias).text,'content':anonymize(payload.content).text})
            if photos:
                session.execute(
                    text('INSERT INTO community_post_photos(post_id,position,image) VALUES (:id,:position,:image)'),
                    [{'id': post_id, 'position': position, 'image': photo} for position, photo in enumerate(photos, 1)],
                )
        return {'status':'pendiente'}
    @router.get('/pending')
    def pending(user=Depends(reviewer)):
        with session_scope() as session:
            return [dict(row) for row in session.execute(text(f"SELECT {POST_FIELDS} FROM community_posts WHERE status='pendiente' ORDER BY created_at")).mappings()]
    def photo_response(post_id, position, status):
        with session_scope() as session:
            image = session.scalar(text("""
                SELECT photos.image FROM community_post_photos AS photos
                JOIN community_posts AS posts ON posts.id=photos.post_id
                WHERE posts.id=:id AND photos.position=:position AND posts.status=:status
            """), {'id': post_id, 'position': position, 'status': status})
        if image is None:
            raise HTTPException(404, 'Foto no disponible.')
        return Response(image, media_type='image/jpeg', headers={'Cache-Control': 'no-store'})

    @router.get('/{post_id}/photos/{position}')
    def public_photo(post_id: UUID, position: int):
        return photo_response(post_id, position, 'publicado')

    @router.get('/{post_id}/photos/{position}/preview')
    def pending_photo(post_id: UUID, position: int, user=Depends(reviewer)):
        return photo_response(post_id, position, 'pendiente')
    @router.post('/{post_id}/review')
    def review(post_id:UUID,payload:Decision,user=Depends(reviewer)):
        if payload.status not in {'publicado','rechazado'}:raise HTTPException(422,'Decisión inválida.')
        with session_scope() as session:
            result=session.execute(text("UPDATE community_posts SET status=:status,reviewer_id=:reviewer WHERE id=:id AND status='pendiente'"),{'id':post_id,'status':payload.status,'reviewer':UUID(user['id'])})
            if not result.rowcount:raise HTTPException(404,'La publicación no está pendiente.')
        return {'status':payload.status}
    return router
