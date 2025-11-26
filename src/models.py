

from flask_sqlalchemy import SQLAlchemy # importa la extension de SQLAlchemy para Flask. 

from sqlalchemy import String, Boolean, Text, ForeignKey, UniqueConstraint, DateTime # constructores que se transforman a SQl
from sqlalchemy.orm import Mapped, mapped_column, relationship # API 
from datetime import datetime #created_at con la hora actual (UTC) en cada registro nuevo
from typing import List  #lista de objetos (1–N o N–N)
from eralchemy2 import render_er  # para generar diagram.png

db = SQLAlchemy()


# TABLA USERS

class User(db.Model):
    __tablename__ = "users"  # plural para evitar conflictos con la palabra reservada "user"

    # columnas principales
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)      # guarda HASH (no texto plano)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # UTC

    # relacion 1–1 
    profile: Mapped["Profile"] = relationship(   # 1–1: un usuario tiene un perfil
        back_populates="user", uselist=False    # devuelve un objeto
    )

    posts: Mapped[List["Post"]] = relationship(  # 1–N: un usuario puede tener muchos posts
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    comments: Mapped[List["Comment"]] = relationship(  # 1–N: un usuario puede tener muchos comentarios
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # N–N  Followers (quien me sigue y a quien sigo)
    followers: Mapped[List["Followers"]] = relationship(  # usuarios que ME siguen
        back_populates="followed",
        foreign_keys="Followers.followed_id"
    )
    following: Mapped[List["Followers"]] = relationship(  # usuarios a los que YO sigo
        back_populates="follower",
        foreign_keys="Followers.follower_id"
    )

    def serialize(self) -> dict:   # convierte el objeto a json, incluye conteos de followers/following
        # Nunca se envia el password!!!
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(), # convierte fechas y horas
            "profile": self.profile.serialize() if self.profile else None,
            "posts": [{"id": p.id, "caption": p.caption} for p in (self.posts or [])],
            "followers_count": len(self.followers or []),
            "following_count": len(self.following or []),
        }



# TABLA PROFILES (perfil)
# 1–1 con usuario

class Profile(db.Model):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str] = mapped_column(String(120), nullable=False) #Biografía
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # UTC fecha de creacion del perfil 

    # clave foranea unique=True → garantiza 1–1, un user_id no puede repetirse en profiles
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
         nullable=False, 
    )

    user: Mapped["User"] = relationship(back_populates="profile", uselist=False) # al reves de la relacion 1–1, permite profile.user

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }



# TABLA POSTS (publicaciones)
# 1–N con usuario

class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # autor del post
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), # si se borra el user → caen sus posts en cascada
        index=True,
        nullable=False, 
    )

    # contenido del post (estilo Instagram)
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    caption: Mapped[str] = mapped_column(String(200), nullable=False) # pie de foto obligatori
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # UTC fecha de creacion del post

    # relaciones
    author: Mapped["User"] = relationship(back_populates="posts", uselist=False) # permite post.author

    # 1–N: un post puede tener muchos comentarios
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_url": self.image_url,
            "caption": self.caption,
            "created_at": self.created_at.isoformat()
        }



# TABLA COMMENTS (comentarios)
# 1–N con post y 1–N con user

class Comment(db.Model):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        index=True,
        nullable=False, 
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False, 
    )

    content: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # UTC

    # relaciones inversas
    post: Mapped["Post"] = relationship(back_populates="comments", uselist=False)
    author: Mapped["User"] = relationship(back_populates="comments", uselist=False)

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }



# TABLA FOLLOWERS 
# N–N  quien sigue a quien

class Followers(db.Model):
    __tablename__ = "followers" #representa el par: follower y followed

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)  # UTC cuando comenzo el follow

    # dos FKs a la MISMA tabla users el que sigue y el seguido
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    followed_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # relaciones hacia User
    follower: Mapped["User"] = relationship(  # el que sigue
        back_populates="following",
        foreign_keys=[follower_id],
        uselist=False
    )
    followed: Mapped["User"] = relationship(  # al que siguen
        back_populates="followers",
        foreign_keys=[followed_id],
        uselist=False
    )

    # evita duplicar a un usuario que siga dos veces  
    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),)

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "follower_id": self.follower_id,
            "followed_id": self.followed_id
        }



# DIBUJAR EL DIAGRAMA

def draw_erd(output_path: str = "diagram.png") -> None:
    """
    Ejecuta:  python src/models.py
    Crea diagram.png con las tablas y relaciones.
    """
    render_er(db.Model, output_path)
    print(f"Diagrama generado en {output_path}")


if __name__ == "__main__":
    draw_erd()