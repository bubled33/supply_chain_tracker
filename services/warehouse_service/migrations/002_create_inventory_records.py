"""
Создание таблицы inventory_records
"""

from yoyo import step

__depends__ = {'001_create_warehouses'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS inventory_records (
            record_id UUID PRIMARY KEY,
            shipment_id UUID NOT NULL,
            warehouse_id UUID NOT NULL REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL,
            received_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_inventory_status 
            CHECK (status IN ('IN_STOCK', 'RESERVED', 'SHIPPED', 'DAMAGED', 'RETURNED'))
        );

        CREATE INDEX idx_inventory_shipment_id ON inventory_records(shipment_id);
        CREATE INDEX idx_inventory_warehouse_id ON inventory_records(warehouse_id);
        CREATE INDEX idx_inventory_status ON inventory_records(status);
        CREATE INDEX idx_inventory_received_at ON inventory_records(received_at);
        CREATE INDEX idx_inventory_warehouse_status ON inventory_records(warehouse_id, status);

        COMMENT ON TABLE inventory_records IS 'Записи инвентаря для отслеживания отгрузок на складах';
        COMMENT ON COLUMN inventory_records.shipment_id IS 'ID отгрузки из shipment_service';
        COMMENT ON COLUMN inventory_records.status IS 'Статус: IN_STOCK, RESERVED, SHIPPED, DAMAGED, RETURNED';
        """,

        # DOWN
        """
        DROP TABLE IF EXISTS inventory_records CASCADE;
        """
    )
]
