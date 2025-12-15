from yoyo import step

__depends__ = {'001_create_couriers'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS deliveries (
            delivery_id UUID PRIMARY KEY,
            shipment_id UUID NOT NULL,
            courier_id UUID NOT NULL REFERENCES couriers(courier_id) ON DELETE RESTRICT,
            status VARCHAR(50) NOT NULL,
            estimated_arrival TIMESTAMPTZ,
            actual_arrival TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_delivery_status 
            CHECK (status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'FAILED', 'CANCELLED')),

            CONSTRAINT ck_arrival_dates
            CHECK (actual_arrival IS NULL OR actual_arrival >= created_at)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_deliveries_shipment_id ON deliveries(shipment_id);
        CREATE INDEX idx_deliveries_courier_id ON deliveries(courier_id);
        CREATE INDEX idx_deliveries_status ON deliveries(status);
        CREATE INDEX idx_deliveries_estimated_arrival ON deliveries(estimated_arrival);
        CREATE INDEX idx_deliveries_actual_arrival ON deliveries(actual_arrival);
        CREATE INDEX idx_deliveries_created_at ON deliveries(created_at DESC);

        -- Композитные индексы для частых запросов
        CREATE INDEX idx_deliveries_courier_status ON deliveries(courier_id, status);
        CREATE INDEX idx_deliveries_shipment_status ON deliveries(shipment_id, status);
        CREATE INDEX idx_deliveries_status_created ON deliveries(status, created_at DESC);

        -- Частичный индекс для активных доставок
        CREATE INDEX idx_deliveries_active 
        ON deliveries(delivery_id, courier_id, estimated_arrival) 
        WHERE status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT');

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_deliveries_updated_at 
            BEFORE UPDATE ON deliveries
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Комментарии
        COMMENT ON TABLE deliveries IS 'Доставки отгрузок курьерами';
        COMMENT ON COLUMN deliveries.delivery_id IS 'Уникальный идентификатор доставки';
        COMMENT ON COLUMN deliveries.shipment_id IS 'ID отгрузки из shipment_service';
        COMMENT ON COLUMN deliveries.courier_id IS 'ID назначенного курьера';
        COMMENT ON COLUMN deliveries.status IS 'Статус доставки: ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, FAILED, CANCELLED';
        COMMENT ON COLUMN deliveries.estimated_arrival IS 'Планируемое время прибытия';
        COMMENT ON COLUMN deliveries.actual_arrival IS 'Фактическое время прибытия';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS update_deliveries_updated_at ON deliveries;
        DROP TABLE IF EXISTS deliveries CASCADE;
        """
    )
]
