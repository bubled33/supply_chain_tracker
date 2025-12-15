"""
Добавление статистики и мониторинга для блокчейн транзакций
"""

from yoyo import step

__depends__ = {'003_create_confirmation_tracking'}

steps = [
    step(
        # UP
        """
        -- Материализованное представление для статистики транзакций
        CREATE MATERIALIZED VIEW blockchain_statistics AS
        SELECT 
            network,
            COUNT(*) as total_transactions,
            COUNT(*) FILTER (WHERE status = 'CONFIRMED') as confirmed,
            COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
            COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
            COUNT(*) FILTER (WHERE status = 'DROPPED') as dropped,
            AVG(EXTRACT(EPOCH FROM (confirmed_at - created_at))) FILTER (WHERE confirmed_at IS NOT NULL) as avg_confirmation_time_seconds,
            SUM(gas_used) FILTER (WHERE gas_used IS NOT NULL) as total_gas_used,
            AVG(gas_used) FILTER (WHERE gas_used IS NOT NULL) as avg_gas_used,
            MIN(created_at) as first_transaction_at,
            MAX(created_at) as last_transaction_at
        FROM blockchain_records
        GROUP BY network;

        CREATE UNIQUE INDEX idx_blockchain_stats_network ON blockchain_statistics(network);

        -- Ежедневная статистика
        CREATE MATERIALIZED VIEW daily_blockchain_statistics AS
        SELECT 
            DATE(created_at) as transaction_date,
            network,
            COUNT(*) as total_transactions,
            COUNT(*) FILTER (WHERE status = 'CONFIRMED') as confirmed,
            COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
            SUM(gas_used) FILTER (WHERE gas_used IS NOT NULL) as total_gas_used,
            AVG(EXTRACT(EPOCH FROM (confirmed_at - created_at))) FILTER (WHERE confirmed_at IS NOT NULL) as avg_confirmation_time_seconds
        FROM blockchain_records
        GROUP BY DATE(created_at), network
        ORDER BY transaction_date DESC, network;

        CREATE UNIQUE INDEX idx_daily_blockchain_stats ON daily_blockchain_statistics(transaction_date, network);

        -- Представление для мониторинга застрявших транзакций
        CREATE VIEW stuck_transactions AS
        SELECT 
            record_id,
            shipment_id,
            tx_hash,
            status,
            created_at,
            EXTRACT(EPOCH FROM (NOW() - created_at)) as pending_duration_seconds,
            gas_price,
            network,
            error_message
        FROM blockchain_records
        WHERE 
            status = 'PENDING' 
            AND created_at < NOW() - INTERVAL '30 minutes'
        ORDER BY created_at ASC;

        -- Представление для успешных транзакций с деталями
        CREATE VIEW confirmed_transactions_summary AS
        SELECT 
            br.record_id,
            br.shipment_id,
            br.tx_hash,
            br.block_number,
            br.confirmed_at,
            br.gas_used,
            br.gas_price,
            br.network,
            EXTRACT(EPOCH FROM (br.confirmed_at - br.created_at)) as confirmation_time_seconds,
            (SELECT MAX(confirmation_count) FROM transaction_confirmations WHERE record_id = br.record_id) as max_confirmations
        FROM blockchain_records br
        WHERE br.status = 'CONFIRMED'
        ORDER BY br.confirmed_at DESC;

        -- Функция для обновления статистики
        CREATE OR REPLACE FUNCTION refresh_blockchain_statistics()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY blockchain_statistics;
            REFRESH MATERIALIZED VIEW CONCURRENTLY daily_blockchain_statistics;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON MATERIALIZED VIEW blockchain_statistics IS 'Общая статистика блокчейн транзакций';
        COMMENT ON MATERIALIZED VIEW daily_blockchain_statistics IS 'Ежедневная статистика блокчейн транзакций';
        COMMENT ON VIEW stuck_transactions IS 'Застрявшие транзакции для мониторинга';
        COMMENT ON VIEW confirmed_transactions_summary IS 'Сводка подтвержденных транзакций с деталями';
        """,

        # DOWN
        """
        DROP FUNCTION IF EXISTS refresh_blockchain_statistics();
        DROP VIEW IF EXISTS confirmed_transactions_summary;
        DROP VIEW IF EXISTS stuck_transactions;
        DROP MATERIALIZED VIEW IF EXISTS daily_blockchain_statistics;
        DROP MATERIALIZED VIEW IF EXISTS blockchain_statistics;
        """
    )
]
