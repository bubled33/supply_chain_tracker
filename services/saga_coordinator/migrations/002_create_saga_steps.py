from yoyo import step

__depends__ = {'001_create_saga_instances'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS saga_steps (
            step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            saga_id UUID NOT NULL REFERENCES saga_instances(saga_id) ON DELETE CASCADE,
            step_name VARCHAR(100) NOT NULL,
            step_order INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            completed_at TIMESTAMPTZ,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0 NOT NULL,
            compensation_data JSONB,

            CONSTRAINT ck_step_status 
            CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'COMPENSATING', 'COMPENSATED')),

            CONSTRAINT ck_step_order CHECK (step_order >= 0),
            CONSTRAINT ck_retry_count CHECK (retry_count >= 0),
            CONSTRAINT ck_step_completed CHECK (completed_at IS NULL OR completed_at >= started_at),

            UNIQUE(saga_id, step_name)
        );

        -- Индексы для оптимизации запросов
        CREATE INDEX idx_saga_steps_saga_id ON saga_steps(saga_id, step_order);
        CREATE INDEX idx_saga_steps_status ON saga_steps(status);
        CREATE INDEX idx_saga_steps_started_at ON saga_steps(started_at DESC);

        -- Композитный индекс для поиска незавершенных шагов
        CREATE INDEX idx_saga_steps_active 
        ON saga_steps(saga_id, step_order) 
        WHERE status IN ('PENDING', 'RUNNING', 'COMPENSATING');

        -- GIN индекс для поиска по JSONB compensation_data
        CREATE INDEX idx_saga_steps_compensation_data ON saga_steps USING GIN(compensation_data);

        -- Комментарии
        COMMENT ON TABLE saga_steps IS 'Шаги выполнения саги для детального трекинга';
        COMMENT ON COLUMN saga_steps.step_name IS 'Название шага (например: CREATE_WAREHOUSE_RECORD)';
        COMMENT ON COLUMN saga_steps.step_order IS 'Порядковый номер шага в саге';
        COMMENT ON COLUMN saga_steps.status IS 'Статус выполнения шага';
        COMMENT ON COLUMN saga_steps.compensation_data IS 'Данные для компенсирующей транзакции в формате JSON';
        COMMENT ON COLUMN saga_steps.retry_count IS 'Количество попыток выполнения шага';
        """,

        # DOWN
        """
        DROP TABLE IF EXISTS saga_steps CASCADE;
        """
    )
]
