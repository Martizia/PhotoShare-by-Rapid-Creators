from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from datetime import date


class Base(DeclarativeBase):
    pass


image_tag = Table('image_tag', Base.metadata,
                  Column('image_id', Integer, ForeignKey('images.id')),
                  Column('tag_id', Integer, ForeignKey('tags.id'))
                  )


image_comment = Table('image_comment', Base.metadata,
                      Column('image_id', Integer, ForeignKey('images.id')),
                      Column('comment_id', Integer, ForeignKey('comments.id'))
                      )


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tags = relationship("Tag", secondary="image_tags", back_populates="images")
    comments = relationship("Comment", back_populates="image")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[date] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now(), nullable=True
    )
    image = relationship("Image", back_populates="comments")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), index=True)
    images = relationship("Image", secondary="image_tags", back_populates="tags")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column("created_at", DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    role: Mapped[str] = mapped_column(String(50), default="user")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)


