from yoyo import step

__depends__ = {'003_add_shipment_metrics'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS shipment_status_history (
            history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            shipment_id UUID NOT NULL REFERENCES shipments(shipment_id) ON DELETE CASCADE,
            old_status VARCHAR(50),
            new_status VARCHAR(50) NOT NULL,
            changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            changed_by VARCHAR(255),
            notes TEXT,
            
            CONSTRAINT ck_status_history_status 
            CHECK (new_status IN ('PENDING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'DELAYED'))
        );
        
        -- Индексы для быстрого поиска истории
        CREATE INDEX idx_status_history_shipment ON shipment_status_history(shipment_id, changed_at DESC);
        CREATE INDEX idx_status_history_status ON shipment_status_history(new_status);
        CREATE INDEX idx_status_history_changed_at ON shipment_status_history(changed_at DESC);
        
        -- Триггер для автоматического логирования изменений статуса
        CREATE OR REPLACE FUNCTION log_shipment_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
                INSERT INTO shipment_status_history (shipment_id, old_status, new_status, changed_at)
                VALUES (NEW.shipment_id, OLD.status, NEW.status, NOW());
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO shipment_status_history (shipment_id, old_status, new_status, changed_at)
                VALUES (NEW.shipment_id, NULL, NEW.status, NOW());
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER track_shipment_status_changes
            AFTER INSERT OR UPDATE OF status ON shipments
            FOR EACH ROW
            EXECUTE FUNCTION log_shipment_status_change();
        
        COMMENT ON TABLE shipment_status_history IS 'История изменения статусов отгрузок для аудита';
        COMMENT ON COLUMN shipment_status_history.old_status IS 'Предыдущий статус (NULL для новых записей)';
        COMMENT ON COLUMN shipment_status_history.new_status IS 'Новый статус';
        COMMENT ON COLUMN shipment_status_history.changed_by IS 'Кто изменил статус (опционально)';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS track_shipment_status_changes ON shipments;
        DROP FUNCTION IF EXISTS log_shipment_status_change();
        DROP TABLE IF EXISTS shipment_status_history CASCADE;
        """
    )
]
