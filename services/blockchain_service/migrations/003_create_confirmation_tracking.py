from yoyo import step

__depends__ = {'002_create_nonce_manager'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS transaction_confirmations (
            confirmation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            record_id UUID NOT NULL REFERENCES blockchain_records(record_id) ON DELETE CASCADE,
            block_number BIGINT NOT NULL,
            confirmation_count INTEGER NOT NULL,
            checked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_block_number CHECK (block_number >= 0),
            CONSTRAINT ck_confirmation_count CHECK (confirmation_count >= 0)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_confirmations_record_id ON transaction_confirmations(record_id, checked_at DESC);
        CREATE INDEX idx_confirmations_block ON transaction_confirmations(block_number);
        CREATE INDEX idx_confirmations_checked ON transaction_confirmations(checked_at DESC);

        -- Таблица для отслеживания событий блокчейна
        CREATE TABLE IF NOT EXISTS blockchain_events (
            event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            record_id UUID NOT NULL REFERENCES blockchain_records(record_id) ON DELETE CASCADE,
            event_name VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            block_number BIGINT NOT NULL,
            transaction_index INTEGER,
            log_index INTEGER,
            detected_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_event_block CHECK (block_number >= 0)
        );

        -- Индексы для событий
        CREATE INDEX idx_blockchain_events_record ON blockchain_events(record_id, detected_at DESC);
        CREATE INDEX idx_blockchain_events_name ON blockchain_events(event_name);
        CREATE INDEX idx_blockchain_events_block ON blockchain_events(block_number);
        CREATE INDEX idx_blockchain_events_data ON blockchain_events USING GIN(event_data);

        -- Комментарии
        COMMENT ON TABLE transaction_confirmations IS 'История подтверждений транзакций в блоках';
        COMMENT ON COLUMN transaction_confirmations.confirmation_count IS 'Количество подтверждений на момент проверки';
        COMMENT ON TABLE blockchain_events IS 'События (events/logs) из блокчейна, связанные с транзакциями';
        COMMENT ON COLUMN blockchain_events.event_name IS 'Название события (например: ShipmentRecorded)';
        COMMENT ON COLUMN blockchain_events.event_data IS 'Данные события из блокчейна';
        """,

        # DOWN
        """
        DROP TABLE IF EXISTS blockchain_events CASCADE;
        DROP TABLE IF EXISTS transaction_confirmations CASCADE;
        """
    )
]
