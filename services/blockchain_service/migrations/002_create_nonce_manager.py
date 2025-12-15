from yoyo import step

__depends__ = {'001_create_blockchain_records'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS nonce_state (
            address VARCHAR(42) PRIMARY KEY,
            current_nonce BIGINT NOT NULL DEFAULT 0,
            network VARCHAR(50) NOT NULL DEFAULT 'ethereum',
            last_updated TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_nonce CHECK (current_nonce >= 0),
            UNIQUE(address, network)
        );

        -- Индекс для быстрого поиска по сети
        CREATE INDEX idx_nonce_network ON nonce_state(network);

        -- Триггер для автообновления last_updated
        CREATE TRIGGER update_nonce_last_updated 
            BEFORE UPDATE ON nonce_state
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Функция для безопасного получения и инкремента nonce
        CREATE OR REPLACE FUNCTION get_next_nonce(wallet_address VARCHAR(42), blockchain_network VARCHAR(50))
        RETURNS BIGINT AS $$
        DECLARE
            next_nonce BIGINT;
        BEGIN
            -- Используем SELECT FOR UPDATE для блокировки строки
            SELECT current_nonce INTO next_nonce
            FROM nonce_state
            WHERE address = wallet_address AND network = blockchain_network
            FOR UPDATE;

            -- Если адрес не найден, создаем новую запись
            IF NOT FOUND THEN
                INSERT INTO nonce_state (address, network, current_nonce)
                VALUES (wallet_address, blockchain_network, 1)
                RETURNING current_nonce INTO next_nonce;
                RETURN 0;
            END IF;

            -- Инкрементируем nonce
            UPDATE nonce_state
            SET current_nonce = current_nonce + 1,
                last_updated = NOW()
            WHERE address = wallet_address AND network = blockchain_network;

            RETURN next_nonce;
        END;
        $$ LANGUAGE plpgsql;

        -- Комментарии
        COMMENT ON TABLE nonce_state IS 'Управление nonce для кошельков при отправке транзакций';
        COMMENT ON COLUMN nonce_state.address IS 'Адрес кошелька (0x...)';
        COMMENT ON COLUMN nonce_state.current_nonce IS 'Текущий nonce для следующей транзакции';
        COMMENT ON COLUMN nonce_state.network IS 'Сеть блокчейна';
        COMMENT ON FUNCTION get_next_nonce IS 'Атомарное получение и инкремент nonce';
        """,

        # DOWN
        """
        DROP FUNCTION IF EXISTS get_next_nonce(VARCHAR, VARCHAR);
        DROP TRIGGER IF EXISTS update_nonce_last_updated ON nonce_state;
        DROP TABLE IF EXISTS nonce_state CASCADE;
        """
    )
]
