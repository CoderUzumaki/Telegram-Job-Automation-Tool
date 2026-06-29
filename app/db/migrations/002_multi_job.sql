-- Multi-job support: one Telegram message can yield multiple inbox rows
ALTER TABLE messages ADD COLUMN job_index INTEGER NOT NULL DEFAULT 0;
ALTER TABLE messages ADD COLUMN job_description TEXT;

-- Replace unique index to include job_index
DROP INDEX IF EXISTS idx_messages_channel_msg;
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_channel_msg_job ON messages(channel_id, message_id, job_index);
