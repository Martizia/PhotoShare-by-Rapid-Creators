import enum
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func, Table, Column, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from datetime import date


class Base(DeclarativeBase):
    pass


image_tag = Table('image_tag', Base.metadata,
                  Column('image_id', Integer, ForeignKey('images.id')),
                  Column('tag_id', Integer, ForeignKey('tags.id'))
                  )


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(String(250), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tags = relationship("Tag", secondary="image_tag", back_populates="images")
    created_at: Mapped[date] = mapped_column("created_at", DateTime, default=func.now(), nullable=True)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    created_at: Mapped[date] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now(), nullable=True
    )


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), index=True)
    images = relationship("Image", secondary="image_tag", back_populates="tags")


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column("created_at", DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    role: Mapped[Enum] = mapped_column(Enum(Role), default=Role.user, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    reset_token: Mapped[str] = mapped_column(String, nullable=True)


class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", backref="ratings", lazy="joined")
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[date] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=False
    )


class TransformedImage(Base):
    __tablename__ = "transformed_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(150), index=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=True)


class Crop(enum.Enum):
    crop: str = "crop"
    scale: str = "scale"
    fill: str = "fill"


class Effect(enum.Enum):
    al_dente: str = "al_dente"
    athena: str = "athena"
    audrey: str = "audrey"
    aurora: str = "aurora"
    daguerre: str = "daguerre"
    fes: str = "fes"
    hairspray: str = "hairspray"
    hokusai: str = "hokusai"
    incognito: str = "incognito"
    linen: str = "linen"
    peacock: str = "peacock"
    primavera: str = "primavera"
    quartz: str = "quartz"
    red_rock: str = "red_rock"
    refresh: str = "refresh"
    sizzle: str = "sizzle"
    sonnet: str = "sonnet"
    ukulele: str = "ukulele"
    zorro: str = "zorro"


class SortBy(enum.Enum):
    rating: str = "rating"
    date: str = "date"
