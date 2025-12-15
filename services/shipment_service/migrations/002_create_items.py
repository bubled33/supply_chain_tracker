from yoyo import step

__depends__ = {'001_create_shipments'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS items (
            item_id UUID PRIMARY KEY,
            shipment_id UUID NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            weight DECIMAL(10, 2) NOT NULL CHECK (weight > 0),
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_items_shipment_id ON items(shipment_id);
        CREATE INDEX idx_items_name ON items(name);
        CREATE INDEX idx_items_quantity ON items(quantity);
        CREATE INDEX idx_items_weight ON items(weight);

        -- Композитный индекс для поиска items конкретной отгрузки
        CREATE INDEX idx_items_shipment_name ON items(shipment_id, name);

        -- GIN индекс для полнотекстового поиска по названию товара
        CREATE INDEX idx_items_name_gin ON items USING GIN(to_tsvector('english', name));

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_items_updated_at 
            BEFORE UPDATE ON items
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Комментарии
        COMMENT ON TABLE items IS 'Товары в отгрузках';
        COMMENT ON COLUMN items.item_id IS 'Уникальный идентификатор товара';
        COMMENT ON COLUMN items.shipment_id IS 'ID отгрузки, к которой относится товар';
        COMMENT ON COLUMN items.name IS 'Название товара';
        COMMENT ON COLUMN items.quantity IS 'Количество товара (должно быть > 0)';
        COMMENT ON COLUMN items.weight IS 'Вес товара в килограммах (должен быть > 0)';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS update_items_updated_at ON items;
        DROP TABLE IF EXISTS items CASCADE;
        """
    )
]
