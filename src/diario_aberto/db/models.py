import datetime as dt
import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import TIMESTAMP, Date, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExtractionStatus(enum.Enum):
    pending = "pending"
    ok = "ok"
    parcial = "parcial_needs_ocr"
    error = "error"


class Edition(Base):
    __tablename__ = "editions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    publication_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    pdf_url: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(Text)
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(
            ExtractionStatus,
            name="status_extracao_enum",
            values_callable=lambda cls: [e.value for e in cls],
        ),
        default=ExtractionStatus.pending,
    )
    collected_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    acts: Mapped[list[Acts]] = relationship(
        back_populates="edition", cascade="all, delete-orphan"
    )


class Acts(Base):
    __tablename__ = "acts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("editions.id"))
    type: Mapped[str | None] = mapped_column(Text)
    act_number: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    edition: Mapped[Edition] = relationship(back_populates="acts")

    @property
    def edition_number(self) -> int:
        return self.edition.number

    @property
    def edition_date(self) -> dt.date:
        return self.edition.publication_date
