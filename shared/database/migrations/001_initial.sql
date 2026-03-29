-- CinemaClip AI — Initial Supabase Migration
-- Run once in Supabase SQL editor

-- Block 1: идеи контента
CREATE TABLE IF NOT EXISTS ideas (
    scene_id        TEXT PRIMARY KEY,           -- e.g. "br2049_royspeech_001"
    film            TEXT NOT NULL,
    year            INTEGER,
    timecode_start  TEXT,                       -- "01:23:45"
    timecode_end    TEXT,                       -- "01:24:30"
    duration_sec    INTEGER,
    description     TEXT,
    hashtags        TEXT,                       -- пробел-разделённые
    theme           TEXT,                       -- запрос пользователя
    why_viral       TEXT,                       -- почему залетит
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      BIGINT                      -- telegram user_id
);

-- Block 1: дедупликация — уже опубликованные сцены
CREATE TABLE IF NOT EXISTS used_scenes (
    scene_id        TEXT PRIMARY KEY REFERENCES ideas(scene_id),
    posted_at       TIMESTAMPTZ DEFAULT NOW(),
    tiktok_url      TEXT,
    notes           TEXT
);

-- Block 2: обработанные клипы
CREATE TABLE IF NOT EXISTS processed_clips (
    id              BIGSERIAL PRIMARY KEY,
    scene_id        TEXT REFERENCES ideas(scene_id),    -- nullable, если без связки
    original_filename TEXT,
    duration_sec    REAL,
    subtitle_mode   TEXT CHECK (subtitle_mode IN ('auto', 'srt')),
    output_size_bytes BIGINT,
    processed_at    TIMESTAMPTZ DEFAULT NOW(),
    processed_by    BIGINT                              -- telegram user_id
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_ideas_created_by ON ideas(created_by);
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clips_processed_by ON processed_clips(processed_by);

-- RLS: разрешаем чтение/запись через anon key (бот использует service key в продакшне)
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE used_scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_clips ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all" ON ideas FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON used_scenes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON processed_clips FOR ALL USING (true) WITH CHECK (true);
