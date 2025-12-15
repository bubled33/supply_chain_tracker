from yoyo import step

__depends__ = {'002_create_inventory_records'}

steps = [
    step(
        # UP
        """
        -- Композитный индекс для поиска по складу и дате
        CREATE INDEX idx_inventory_warehouse_received 
        ON inventory_records(warehouse_id, received_at DESC);

        -- Частичный индекс только для активных записей
        CREATE INDEX idx_inventory_active 
        ON inventory_records(warehouse_id, shipment_id) 
        WHERE status IN ('IN_STOCK', 'RESERVED');
        """,

        # DOWN
        """
        DROP INDEX IF EXISTS idx_inventory_warehouse_received;
        DROP INDEX IF EXISTS idx_inventory_active;
        """
    )
]
