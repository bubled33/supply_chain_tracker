from yoyo import step

__depends__ = {'002_create_items'}

steps = [
    step(
        # UP
        """
        -- Частичный индекс для активных отгрузок
        CREATE INDEX idx_shipments_active 
        ON shipments(shipment_id, status, created_at) 
        WHERE status IN ('PENDING', 'IN_TRANSIT');

        -- Индекс для подсчета общего веса по отгрузке
        CREATE INDEX idx_items_shipment_weight ON items(shipment_id, weight);

        -- Материализованное представление для статистики по отгрузкам
        CREATE MATERIALIZED VIEW shipment_statistics AS
        SELECT 
            s.shipment_id,
            s.status,
            s.origin,
            s.destination,
            COUNT(i.item_id) as total_items,
            COALESCE(SUM(i.quantity), 0) as total_quantity,
            COALESCE(SUM(i.weight), 0) as total_weight,
            s.created_at,
            s.updated_at
        FROM shipments s
        LEFT JOIN items i ON s.shipment_id = i.shipment_id
        GROUP BY s.shipment_id, s.status, s.origin, s.destination, s.created_at, s.updated_at;

        -- Индекс на материализованном представлении
        CREATE INDEX idx_shipment_stats_id ON shipment_statistics(shipment_id);
        CREATE INDEX idx_shipment_stats_status ON shipment_statistics(status);

        -- Функция для обновления материализованного представления
        CREATE OR REPLACE FUNCTION refresh_shipment_statistics()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY shipment_statistics;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON MATERIALIZED VIEW shipment_statistics IS 'Статистика по отгрузкам с агрегированными данными';
        """,

        # DOWN
        """
        DROP FUNCTION IF EXISTS refresh_shipment_statistics();
        DROP MATERIALIZED VIEW IF EXISTS shipment_statistics;
        DROP INDEX IF EXISTS idx_items_shipment_weight;
        DROP INDEX IF EXISTS idx_shipments_active;
        """
    )
]
