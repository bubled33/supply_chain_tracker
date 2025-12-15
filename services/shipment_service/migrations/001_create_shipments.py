from yoyo import step

__depends__ = {}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id UUID PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_shipment_status 
            CHECK (status IN ('PENDING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'DELAYED'))
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_shipments_status ON shipments(status);
        CREATE INDEX idx_shipments_created_at ON shipments(created_at DESC);
        CREATE INDEX idx_shipments_updated_at ON shipments(updated_at DESC);

        -- Композитный индекс для поиска по статусу и дате
        CREATE INDEX idx_shipments_status_created ON shipments(status, created_at DESC);

        -- GIN индекс для полнотекстового поиска по origin/destination
        CREATE INDEX idx_shipments_origin_gin ON shipments USING GIN(to_tsvector('english', origin));
        CREATE INDEX idx_shipments_destination_gin ON shipments USING GIN(to_tsvector('english', destination));

        -- Функция для автообновления updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_shipments_updated_at 
            BEFORE UPDATE ON shipments
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Комментарии
        COMMENT ON TABLE shipments IS 'Отгрузки в системе управления цепочками поставок';
        COMMENT ON COLUMN shipments.shipment_id IS 'Уникальный идентификатор отгрузки';
        COMMENT ON COLUMN shipments.origin IS 'Место отправления в формате JSON: {"country": "...", "city": "...", "address": "..."}';
        COMMENT ON COLUMN shipments.destination IS 'Место назначения в формате JSON';
        COMMENT ON COLUMN shipments.status IS 'Статус отгрузки: PENDING, IN_TRANSIT, DELIVERED, CANCELLED, DELAYED';
        COMMENT ON COLUMN shipments.created_at IS 'Дата создания отгрузки';
        COMMENT ON COLUMN shipments.updated_at IS 'Дата последнего обновления';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS update_shipments_updated_at ON shipments;
        DROP FUNCTION IF EXISTS update_updated_at_column();
        DROP TABLE IF EXISTS shipments CASCADE;
        """
    )
]
