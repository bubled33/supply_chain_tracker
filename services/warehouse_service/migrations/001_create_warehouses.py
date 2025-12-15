"""
Создание таблицы warehouses
"""

from yoyo import step

__depends__ = {}

steps = [
    step(

        """
        CREATE TABLE IF NOT EXISTS warehouses (
            warehouse_id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );

        CREATE INDEX idx_warehouses_name ON warehouses(name);
        CREATE INDEX idx_warehouses_location ON warehouses USING GIN(to_tsvector('english', location));

        COMMENT ON TABLE warehouses IS 'Склады для хранения отгрузок';
        COMMENT ON COLUMN warehouses.warehouse_id IS 'Уникальный идентификатор склада';
        COMMENT ON COLUMN warehouses.name IS 'Название склада';
        COMMENT ON COLUMN warehouses.location IS 'Адрес склада в формате JSON';
        """,


        """
        DROP TABLE IF EXISTS warehouses CASCADE;
        """
    )
]
