from yoyo import step

__depends__ = {'002_create_saga_steps'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS saga_events (
            event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            saga_id UUID NOT NULL REFERENCES saga_instances(saga_id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            occurred_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

            CONSTRAINT ck_event_type 
            CHECK (event_type IN (
                'SAGA_STARTED', 
                'STEP_STARTED', 
                'STEP_COMPLETED', 
                'STEP_FAILED',
                'COMPENSATION_STARTED',
                'COMPENSATION_COMPLETED',
                'SAGA_COMPLETED',
                'SAGA_FAILED'
            ))
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_saga_events_saga_id ON saga_events(saga_id, occurred_at DESC);
        CREATE INDEX idx_saga_events_type ON saga_events(event_type);
        CREATE INDEX idx_saga_events_occurred_at ON saga_events(occurred_at DESC);

        -- GIN индекс для поиска по event_data
        CREATE INDEX idx_saga_events_data ON saga_events USING GIN(event_data);

        -- Функция для автоматического логирования событий саги
        CREATE OR REPLACE FUNCTION log_saga_event()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                INSERT INTO saga_events (saga_id, event_type, event_data)
                VALUES (
                    NEW.saga_id, 
                    'SAGA_STARTED', 
                    jsonb_build_object(
                        'saga_type', NEW.saga_type,
                        'shipment_id', NEW.shipment_id,
                        'status', NEW.status
                    )
                );
            ELSIF (TG_OP = 'UPDATE' AND OLD.status != NEW.status) THEN
                INSERT INTO saga_events (saga_id, event_type, event_data)
                VALUES (
                    NEW.saga_id,
                    CASE 
                        WHEN NEW.status = 'COMPLETED' THEN 'SAGA_COMPLETED'
                        WHEN NEW.status = 'FAILED' THEN 'SAGA_FAILED'
                        WHEN NEW.status = 'COMPENSATING' THEN 'COMPENSATION_STARTED'
                        ELSE 'SAGA_STARTED'
                    END,
                    jsonb_build_object(
                        'old_status', OLD.status,
                        'new_status', NEW.status,
                        'failed_step', NEW.failed_step,
                        'error_message', NEW.error_message
                    )
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER track_saga_events
            AFTER INSERT OR UPDATE OF status ON saga_instances
            FOR EACH ROW
            EXECUTE FUNCTION log_saga_event();

        -- Комментарии
        COMMENT ON TABLE saga_events IS 'Event sourcing для саг - полная история всех событий';
        COMMENT ON COLUMN saga_events.event_type IS 'Тип события в жизненном цикле саги';
        COMMENT ON COLUMN saga_events.event_data IS 'Данные события в формате JSON';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS track_saga_events ON saga_instances;
        DROP FUNCTION IF EXISTS log_saga_event();
        DROP TABLE IF EXISTS saga_events CASCADE;
        """
    )
]
