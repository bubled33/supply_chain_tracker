
from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.last_updated = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TYPE blockchain_tx_status AS ENUM ('PENDING', 'CONFIRMED', 'FAILED', 'DROPPED');

        CREATE TABLE IF NOT EXISTS blockchain_records (
            record_id     UUID PRIMARY KEY,
            shipment_id   UUID NOT NULL,
            tx_hash       VARCHAR(255) NOT NULL UNIQUE,
            status        blockchain_tx_status NOT NULL DEFAULT 'PENDING',
            payload       JSONB NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL,
            confirmed_at  TIMESTAMPTZ,
            block_number  BIGINT,
            error_message TEXT,
            gas_used      BIGINT,
            gas_price     BIGINT,
            network       VARCHAR(50) NOT NULL DEFAULT 'ethereum'
        );

        CREATE INDEX idx_blockchain_records_status ON blockchain_records(status);
        CREATE INDEX idx_blockchain_records_shipment_id ON blockchain_records(shipment_id);
        CREATE INDEX idx_blockchain_records_tx_hash ON blockchain_records(tx_hash);
        CREATE INDEX idx_blockchain_records_network ON blockchain_records(network);
        """,

        """
        DROP TABLE IF EXISTS blockchain_records CASCADE;
        DROP TYPE IF EXISTS blockchain_tx_status;
        DROP FUNCTION IF EXISTS update_updated_at_column();
        """
    )
]
