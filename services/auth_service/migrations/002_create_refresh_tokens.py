from yoyo import step

__depends__ = {"001_create_users"}

steps = [
    step(
        """
        CREATE TABLE refresh_tokens (
            token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "DROP TABLE refresh_tokens;",
    )
]
