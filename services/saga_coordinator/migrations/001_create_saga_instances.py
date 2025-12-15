from yoyo import step

__depends__ = {}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS saga_instances (
            saga_id UUID PRIMARY KEY,
            saga_type VARCHAR(100) NOT NULL,
            shipment_id UUID NOT NULL,
            warehouse_id UUID,
            delivery_id UUID,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            completed_at TIMESTAMPTZ,
            failed_step VARCHAR(100),
            error_message TEXT,
            retry_count INTEGER DEFAULT 0 NOT NULL,

            CONSTRAINT ck_saga_status 
            CHECK (status IN ('STARTED', 'COMPENSATING', 'COMPLETED', 'FAILED', 'CANCELLED')),

            CONSTRAINT ck_retry_count CHECK (retry_count >= 0),

            CONSTRAINT ck_completed_at 
            CHECK (completed_at IS NULL OR completed_at >= started_at)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_saga_shipment_id ON saga_instances(shipment_id);
        CREATE INDEX idx_saga_status ON saga_instances(status);
        CREATE INDEX idx_saga_started_at ON saga_instances(started_at DESC);
        CREATE INDEX idx_saga_updated_at ON saga_instances(updated_at DESC);
        CREATE INDEX idx_saga_type ON saga_instances(saga_type);

        -- Композитные индексы для частых запросов
        CREATE INDEX idx_saga_status_updated ON saga_instances(status, updated_at ASC);
        CREATE INDEX idx_saga_type_status ON saga_instances(saga_type, status);

        -- Частичные индексы для активных саг
        CREATE INDEX idx_saga_active 
        ON saga_instances(saga_id, shipment_id, updated_at) 
        WHERE status IN ('STARTED', 'COMPENSATING');

        -- Уникальный индекс для предотвращения дублирования активных саг на один shipment
        CREATE UNIQUE INDEX idx_saga_shipment_active 
        ON saga_instances(shipment_id) 
        WHERE status IN ('STARTED', 'COMPENSATING');

        -- Функция для автообновления updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Триггер для автообновления updated_at
        CREATE TRIGGER update_saga_updated_at 
            BEFORE UPDATE ON saga_instances
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Триггер для установки completed_at при завершении саги
        CREATE OR REPLACE FUNCTION set_saga_completed_at()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') AND OLD.status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
                NEW.completed_at = NOW();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER set_saga_completion_time
            BEFORE UPDATE OF status ON saga_instances
            FOR EACH ROW
            EXECUTE FUNCTION set_saga_completed_at();

        -- Комментарии
        COMMENT ON TABLE saga_instances IS 'Инстансы SAGA паттерна для координации распределенных транзакций';
        COMMENT ON COLUMN saga_instances.saga_id IS 'Уникальный идентификатор саги';
        COMMENT ON COLUMN saga_instances.saga_type IS 'Тип саги (например: CREATE_SHIPMENT, UPDATE_DELIVERY)';
        COMMENT ON COLUMN saga_instances.shipment_id IS 'ID отгрузки, для которой запущена сага';
        COMMENT ON COLUMN saga_instances.warehouse_id IS 'ID склада (если применимо)';
        COMMENT ON COLUMN saga_instances.delivery_id IS 'ID доставки (если применимо)';
        COMMENT ON COLUMN saga_instances.status IS 'Статус саги: STARTED, COMPENSATING, COMPLETED, FAILED, CANCELLED';
        COMMENT ON COLUMN saga_instances.started_at IS 'Время начала саги';
        COMMENT ON COLUMN saga_instances.updated_at IS 'Время последнего обновления';
        COMMENT ON COLUMN saga_instances.completed_at IS 'Время завершения саги';
        COMMENT ON COLUMN saga_instances.failed_step IS 'Название шага, на котором произошел сбой';
        COMMENT ON COLUMN saga_instances.error_message IS 'Сообщение об ошибке';
        COMMENT ON COLUMN saga_instances.retry_count IS 'Количество попыток повтора';
        """,

        # DOWN
        """
        DROP TRIGGER IF EXISTS set_saga_completion_time ON saga_instances;
        DROP FUNCTION IF EXISTS set_saga_completed_at();
        DROP TRIGGER IF EXISTS update_saga_updated_at ON saga_instances;
        DROP FUNCTION IF EXISTS update_updated_at_column();
        DROP TABLE IF EXISTS saga_instances CASCADE;
        """
    )
]
