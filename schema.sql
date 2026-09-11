CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS edicoes (
    id              SERIAL PRIMARY KEY,
    numero          INTEGER NOT NULL UNIQUE,
    data_publicacao DATE NOT NULL,
    url_pdf         TEXT NOT NULL,
    caminho_pdf     TEXT,
    status_extracao TEXT NOT NULL DEFAULT 'pendente',
    coletado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edicoes_data ON edicoes (data_publicacao);
CREATE INDEX IF NOT EXISTS idx_edicoes_status ON edicoes (status_extracao);

-- Cada "ato" é uma unidade administrativa individual dentro de uma edição
-- (uma Portaria, um Decreto, um Edital específico) — ver extraction/segmentation.py.
-- É essa granularidade que o Querido Diário NÃO faz (eles indexam a edição inteira),
-- então segmentar por ato é um diferencial técnico real do seu projeto, não só um capricho.
CREATE TABLE IF NOT EXISTS atos (
    id           SERIAL PRIMARY KEY,
    edicao_id    INTEGER NOT NULL REFERENCES edicoes(id) ON DELETE CASCADE,
    tipo         TEXT,            -- 'portaria' | 'decreto' | 'edital' | 'outro'
    numero_ato   TEXT,
    texto        TEXT NOT NULL,
    pagina       INTEGER,
    tsv          TSVECTOR GENERATED ALWAYS AS (to_tsvector('portuguese', texto)) STORED,
    embedding    VECTOR(1536),    -- dimensão do text-embedding-3-small; ajuste se trocar de modelo
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_atos_tsv ON atos USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_atos_edicao ON atos (edicao_id);

-- Índice HNSW para busca vetorial aproximada
-- CREATE INDEX idx_atos_embedding ON atos USING hnsw (embedding vector_cosine_ops);
