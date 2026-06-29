PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    posted_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    extraction TEXT NOT NULL DEFAULT '{}',
    parser_version INTEGER NOT NULL DEFAULT 0,
    parser_matched INTEGER NOT NULL DEFAULT 0,
    filter_passed INTEGER NOT NULL DEFAULT 0,
    relevance_score INTEGER,
    relevance_reason TEXT,
    profile_version_scored INTEGER,
    filter_rules_version_scored INTEGER,
    llm_schema_version INTEGER,
    processing_state TEXT NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    last_error_stage TEXT,
    last_error_at TEXT,
    parser_attempts INTEGER NOT NULL DEFAULT 0,
    llm_attempts INTEGER NOT NULL DEFAULT 0,
    review_state TEXT NOT NULL DEFAULT 'none',
    reviewed_at TEXT,
    export_state TEXT NOT NULL DEFAULT 'none',
    export_error TEXT,
    export_attempts INTEGER NOT NULL DEFAULT 0,
    sheet_row_id TEXT,
    exported_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_channel_msg ON messages(channel_id, message_id);
CREATE INDEX IF NOT EXISTS idx_messages_inbox ON messages(review_state, relevance_score DESC)
    WHERE review_state = 'inbox';
CREATE INDEX IF NOT EXISTS idx_messages_pipeline ON messages(processing_state)
    WHERE processing_state IN ('pending', 'error');
CREATE INDEX IF NOT EXISTS idx_messages_posted ON messages(posted_at DESC);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    domain TEXT NOT NULL,
    position INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_links_message ON links(message_id);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);
