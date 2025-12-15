from yoyo import step

__depends__ = {}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS couriers (
            courier_id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            contact_info TEXT NOT NULL,
            is_active BOOLEAN DEFAULT true NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_couriers_name ON couriers(name);
        CREATE INDEX idx_couriers_active ON couriers(is_active) WHERE is_active = true;

        -- GIN индекс для полнотекстового поиска по имени
        CREATE INDEX idx_couriers_name_gin ON couriers USING GIN(to_tsvector('english', name));

        -- Функция для автообновления updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_couriers_updated_at 
            BEFORE UPDATE ON couriers
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Комментарии
        COMMENT ON TABLE couriers IS 'Курьеры для доставки отгрузок';
        COMMENT ON COLUMN couriers.courier_id IS 'Уникальный идентификатор курьера';
        COMMENT ON COLUMN couriers.name IS 'ФИО курьера';
        COMMENT ON COLUMN couriers.contact_info IS 'Контактная информация в формате JSON: {"phone": "...", "email": "..."}';
        COMMENT ON COLUMN couriers.is_active IS 'Флаг активности курьера';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS update_couriers_updated_at ON couriers;
        DROP FUNCTION IF EXISTS update_updated_at_column();
        DROP TABLE IF EXISTS couriers CASCADE;
        """
    )
]
