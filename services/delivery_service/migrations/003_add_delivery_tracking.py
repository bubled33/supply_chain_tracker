from yoyo import step

__depends__ = {'002_create_deliveries'}

steps = [
    step(
        # UP
        """
        CREATE TABLE IF NOT EXISTS delivery_tracking_points (
            tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            delivery_id UUID NOT NULL REFERENCES deliveries(delivery_id) ON DELETE CASCADE,
            latitude DECIMAL(10, 8) NOT NULL,
            longitude DECIMAL(11, 8) NOT NULL,
            accuracy_meters INTEGER,
            recorded_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
            notes TEXT,

            CONSTRAINT ck_latitude CHECK (latitude >= -90 AND latitude <= 90),
            CONSTRAINT ck_longitude CHECK (longitude >= -180 AND longitude <= 180),
            CONSTRAINT ck_accuracy CHECK (accuracy_meters IS NULL OR accuracy_meters > 0)
        );

        -- Индексы для поиска точек трекинга
        CREATE INDEX idx_tracking_delivery ON delivery_tracking_points(delivery_id, recorded_at DESC);
        CREATE INDEX idx_tracking_recorded_at ON delivery_tracking_points(recorded_at DESC);

        -- Пространственный индекс для геопозиционирования (PostGIS не требуется)
        CREATE INDEX idx_tracking_location ON delivery_tracking_points(latitude, longitude);

        COMMENT ON TABLE delivery_tracking_points IS 'Точки геолокации для отслеживания доставок в реальном времени';
        COMMENT ON COLUMN delivery_tracking_points.latitude IS 'Широта (-90 до 90)';
        COMMENT ON COLUMN delivery_tracking_points.longitude IS 'Долгота (-180 до 180)';
        COMMENT ON COLUMN delivery_tracking_points.accuracy_meters IS 'Точность позиции в метрах';
        """,

        # DOWN
        """
        DROP TABLE IF EXISTS delivery_tracking_points CASCADE;
        """
    )
]
