from yoyo import step

__depends__ = {'003_create_saga_events'}

steps = [
    step(
        # UP
        """
        -- Материализованное представление для общей статистики саг
        CREATE MATERIALIZED VIEW saga_statistics AS
        SELECT 
            saga_type,
            COUNT(*) as total_sagas,
            COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed,
            COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
            COUNT(*) FILTER (WHERE status = 'CANCELLED') as cancelled,
            COUNT(*) FILTER (WHERE status IN ('STARTED', 'COMPENSATING')) as in_progress,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE completed_at IS NOT NULL) as avg_duration_seconds,
            MAX(retry_count) as max_retry_count,
            AVG(retry_count) as avg_retry_count
        FROM saga_instances
        GROUP BY saga_type;

        CREATE UNIQUE INDEX idx_saga_stats_type ON saga_statistics(saga_type);

        -- Материализованное представление для ежедневной статистики
        CREATE MATERIALIZED VIEW daily_saga_statistics AS
        SELECT 
            DATE(started_at) as saga_date,
            saga_type,
            COUNT(*) as total_sagas,
            COUNT(*) FILTER (WHERE status = 'COMPLETED') as completed,
            COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FILTER (WHERE completed_at IS NOT NULL) as avg_duration_seconds
        FROM saga_instances
        GROUP BY DATE(started_at), saga_type
        ORDER BY saga_date DESC, saga_type;

        CREATE UNIQUE INDEX idx_daily_saga_stats ON daily_saga_statistics(saga_date, saga_type);

        -- Представление для мониторинга зависших саг
        CREATE VIEW stuck_sagas AS
        SELECT 
            saga_id,
            saga_type,
            shipment_id,
            status,
            started_at,
            updated_at,
            EXTRACT(EPOCH FROM (NOW() - updated_at)) as stuck_duration_seconds,
            retry_count,
            failed_step,
            error_message
        FROM saga_instances
        WHERE 
            status IN ('STARTED', 'COMPENSATING') 
            AND updated_at < NOW() - INTERVAL '10 minutes'
        ORDER BY updated_at ASC;

        -- Функция для обновления статистики
        CREATE OR REPLACE FUNCTION refresh_saga_statistics()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY saga_statistics;
            REFRESH MATERIALIZED VIEW CONCURRENTLY daily_saga_statistics;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON MATERIALIZED VIEW saga_statistics IS 'Общая статистика выполнения саг по типам';
        COMMENT ON MATERIALIZED VIEW daily_saga_statistics IS 'Ежедневная статистика выполнения саг';
        COMMENT ON VIEW stuck_sagas IS 'Зависшие саги для мониторинга и восстановления';
        """,

        # DOWN
        """
        DROP FUNCTION IF EXISTS refresh_saga_statistics();
        DROP VIEW IF EXISTS stuck_sagas;
        DROP MATERIALIZED VIEW IF EXISTS daily_saga_statistics;
        DROP MATERIALIZED VIEW IF EXISTS saga_statistics;
        """
    )
]
