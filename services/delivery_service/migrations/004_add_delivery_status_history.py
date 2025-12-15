from yoyo import step

__depends__ = {'003_add_delivery_tracking'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS delivery_status_history (
            history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            delivery_id UUID NOT NULL REFERENCES deliveries(delivery_id) ON DELETE CASCADE,
            old_status VARCHAR(50),
            new_status VARCHAR(50) NOT NULL,
            changed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            changed_by VARCHAR(255),
            notes TEXT,

            CONSTRAINT ck_status_history_status 
            CHECK (new_status IN ('ASSIGNED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'FAILED', 'CANCELLED'))
        );

        -- Индексы для быстрого поиска истории
        CREATE INDEX idx_delivery_status_history_delivery ON delivery_status_history(delivery_id, changed_at DESC);
        CREATE INDEX idx_delivery_status_history_status ON delivery_status_history(new_status);
        CREATE INDEX idx_delivery_status_history_changed_at ON delivery_status_history(changed_at DESC);

        -- Триггер для автоматического логирования изменений статуса
        CREATE OR REPLACE FUNCTION log_delivery_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
                INSERT INTO delivery_status_history (delivery_id, old_status, new_status, changed_at)
                VALUES (NEW.delivery_id, OLD.status, NEW.status, NOW());
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO delivery_status_history (delivery_id, old_status, new_status, changed_at)
                VALUES (NEW.delivery_id, NULL, NEW.status, NOW());
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER track_delivery_status_changes
            AFTER INSERT OR UPDATE OF status ON deliveries
            FOR EACH ROW
            EXECUTE FUNCTION log_delivery_status_change();

        COMMENT ON TABLE delivery_status_history IS 'История изменения статусов доставок для аудита';
        COMMENT ON COLUMN delivery_status_history.old_status IS 'Предыдущий статус (NULL для новых записей)';
        COMMENT ON COLUMN delivery_status_history.new_status IS 'Новый статус';
        COMMENT ON COLUMN delivery_status_history.changed_by IS 'Кто изменил статус (опционально)';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS track_delivery_status_changes ON deliveries;
        DROP FUNCTION IF EXISTS log_delivery_status_change();
        DROP TABLE IF EXISTS delivery_status_history CASCADE;
        """
    )
]
