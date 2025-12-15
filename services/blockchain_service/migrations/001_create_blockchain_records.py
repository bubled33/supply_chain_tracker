from yoyo import step

__depends__ = {}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS blockchain_records (
            record_id UUID PRIMARY KEY,
            shipment_id UUID NOT NULL,
            tx_hash VARCHAR(66) UNIQUE NOT NULL,
            status VARCHAR(50) NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            confirmed_at TIMESTAMPTZ,
            block_number BIGINT,
            error_message TEXT,
            gas_used BIGINT,
            gas_price BIGINT,
            network VARCHAR(50) DEFAULT 'ethereum' NOT NULL,

            CONSTRAINT ck_blockchain_status 
            CHECK (status IN ('PENDING', 'CONFIRMED', 'FAILED', 'DROPPED')),

            CONSTRAINT ck_block_number CHECK (block_number IS NULL OR block_number >= 0),
            CONSTRAINT ck_gas_used CHECK (gas_used IS NULL OR gas_used >= 0),
            CONSTRAINT ck_gas_price CHECK (gas_price IS NULL OR gas_price >= 0),
            CONSTRAINT ck_confirmed_at CHECK (confirmed_at IS NULL OR confirmed_at >= created_at)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_blockchain_shipment_id ON blockchain_records(shipment_id);
        CREATE INDEX idx_blockchain_tx_hash ON blockchain_records(tx_hash);
        CREATE INDEX idx_blockchain_status ON blockchain_records(status);
        CREATE INDEX idx_blockchain_created_at ON blockchain_records(created_at DESC);
        CREATE INDEX idx_blockchain_confirmed_at ON blockchain_records(confirmed_at DESC) WHERE confirmed_at IS NOT NULL;
        CREATE INDEX idx_blockchain_block_number ON blockchain_records(block_number DESC) WHERE block_number IS NOT NULL;
        CREATE INDEX idx_blockchain_network ON blockchain_records(network);

        -- Композитные индексы для частых запросов
        CREATE INDEX idx_blockchain_status_created ON blockchain_records(status, created_at ASC);
        CREATE INDEX idx_blockchain_shipment_status ON blockchain_records(shipment_id, status);

        -- Частичный индекс для pending транзакций (для мониторинга)
        CREATE INDEX idx_blockchain_pending 
        ON blockchain_records(record_id, created_at ASC) 
        WHERE status = 'PENDING';

        -- GIN индекс для поиска по JSONB payload
        CREATE INDEX idx_blockchain_payload ON blockchain_records USING GIN(payload);

        -- Функция для автообновления updated_at (если добавим поле)
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Добавим поле updated_at
        ALTER TABLE blockchain_records ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_blockchain_updated_at 
            BEFORE UPDATE ON blockchain_records
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Комментарии
        COMMENT ON TABLE blockchain_records IS 'Записи транзакций в блокчейне для отгрузок';
        COMMENT ON COLUMN blockchain_records.record_id IS 'Уникальный идентификатор записи';
        COMMENT ON COLUMN blockchain_records.shipment_id IS 'ID отгрузки из shipment_service';
        COMMENT ON COLUMN blockchain_records.tx_hash IS 'Хеш транзакции в блокчейне (0x...)';
        COMMENT ON COLUMN blockchain_records.status IS 'Статус транзакции: PENDING, CONFIRMED, FAILED, DROPPED';
        COMMENT ON COLUMN blockchain_records.payload IS 'Данные транзакции в формате JSON';
        COMMENT ON COLUMN blockchain_records.created_at IS 'Время создания транзакции';
        COMMENT ON COLUMN blockchain_records.confirmed_at IS 'Время подтверждения транзакции в блокчейне';
        COMMENT ON COLUMN blockchain_records.block_number IS 'Номер блока, в который включена транзакция';
        COMMENT ON COLUMN blockchain_records.error_message IS 'Сообщение об ошибке при неудачной транзакции';
        COMMENT ON COLUMN blockchain_records.gas_used IS 'Количество использованного газа';
        COMMENT ON COLUMN blockchain_records.gas_price IS 'Цена газа в Wei';
        COMMENT ON COLUMN blockchain_records.network IS 'Сеть блокчейна (ethereum, polygon, etc.)';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS update_blockchain_updated_at ON blockchain_records;
        DROP FUNCTION IF EXISTS update_updated_at_column();
        DROP TABLE IF EXISTS blockchain_records CASCADE;
        """
    )
]
