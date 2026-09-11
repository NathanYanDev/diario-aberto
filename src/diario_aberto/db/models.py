import datetime as dt
import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import TIMESTAMP, Date, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StatusExtracao(enum.Enum):
    pendente = "pendente"
    ok = "ok"
    parcial = "parcial_precisa_ocr"
    erro = "erro"


class Edicao(Base):
    __tablename__ = "edicoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    data_publicacao: Mapped[dt.date] = mapped_column(Date, nullable=False)
    url_pdf: Mapped[str] = mapped_column(Text, nullable=False)
    caminho_pdf: Mapped[str | None] = mapped_column(Text)
    status_extracao: Mapped[StatusExtracao] = mapped_column(
        Enum(
            StatusExtracao,
            name="status_extracao_enum",
            values_callable=lambda cls: [e.value for e in cls],
        ),
        default=StatusExtracao.pendente,
    )
    coletado_em: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    atos: Mapped[list[Ato]] = relationship(
        back_populates="edicao", cascade="all, delete-orphan"
    )


class Ato(Base):
    __tablename__ = "atos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edicao_id: Mapped[int] = mapped_column(ForeignKey("edicoes.id"))
    tipo: Mapped[str | None] = mapped_column(Text)
    numero_ato: Mapped[str | None] = mapped_column(Text)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    pagina: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=False)
    criado_em: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    edicao: Mapped[Edicao] = relationship(back_populates="atos")

    @property
    def edicao_numero(self) -> int:
        return self.edicao.numero

    @property
    def edicao_data(self) -> dt.date:
        return self.edicao.data_publicacao
