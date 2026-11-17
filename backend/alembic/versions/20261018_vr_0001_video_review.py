"""Frozen owned09 schema. Apply only to an explicitly authorized database."""

from alembic import op

revision = "20261018_vr_0001"
down_revision = None
branch_labels = ("video_review",)
depends_on = None

DDL = r"""
CREATE TABLE video_review.head (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 video_id VARCHAR(120) NOT NULL, revision BIGINT NOT NULL,
 subject_digest VARCHAR(64) NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id,session_id,video_id),
 CONSTRAINT head_revision CHECK (revision > 0),
 CONSTRAINT head_digest CHECK (subject_digest ~ '^[0-9a-f]{64}$'),
 CONSTRAINT head_object CHECK (jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_review.receipt (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 video_id VARCHAR(120) NOT NULL, principal_id VARCHAR(120) NOT NULL,
 client_key VARCHAR(120) NOT NULL, kind VARCHAR(16) NOT NULL,
 revision BIGINT NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id,session_id,video_id,principal_id,client_key),
 CONSTRAINT receipt_kind CHECK (kind IN ('write','change')),
 CONSTRAINT receipt_revision CHECK (revision > 0),
 CONSTRAINT receipt_object CHECK (jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_review.history (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 video_id VARCHAR(120) NOT NULL, revision BIGINT NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id,session_id,video_id,revision),
 CONSTRAINT history_revision CHECK (revision > 0),
 CONSTRAINT history_object CHECK (jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_review.playback (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 principal_id VARCHAR(120) NOT NULL, client_key VARCHAR(120) NOT NULL,
 video_id VARCHAR(120) NOT NULL, revision BIGINT NOT NULL,
 state VARCHAR(16) NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id,session_id,principal_id,client_key),
 CONSTRAINT playback_revision CHECK (revision IN (1,2)),
 CONSTRAINT playback_state CHECK (state IN ('pending','playing','rejected')),
 CONSTRAINT playback_object CHECK (jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_review.playback_history (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 principal_id VARCHAR(120) NOT NULL, client_key VARCHAR(120) NOT NULL,
 revision BIGINT NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id,session_id,principal_id,client_key,revision),
 CONSTRAINT ph_revision CHECK (revision IN (1,2)),
 CONSTRAINT ph_object CHECK (jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_review.event (
 organization_id VARCHAR(120) NOT NULL, event_id VARCHAR(200) NOT NULL,
 session_id VARCHAR(120) NOT NULL, video_id VARCHAR(120) NOT NULL,
 kind VARCHAR(40) NOT NULL, revision BIGINT NOT NULL, subject_digest VARCHAR(64) NOT NULL,
 PRIMARY KEY (organization_id,event_id),
 CONSTRAINT event_scoped_identity UNIQUE (organization_id,session_id,video_id,kind,event_id),
 CONSTRAINT event_revision CHECK (revision > 0),
 CONSTRAINT event_digest CHECK (subject_digest ~ '^[0-9a-f]{64}$')
);
"""

IMMUTABLE = r"""
CREATE FUNCTION video_review.immutable_row() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'video review immutable history'; END; $$
"""
HEAD_GUARD = r"""
CREATE FUNCTION video_review.guard_head() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'video review head delete forbidden'; END IF;
 IF (NEW.organization_id,NEW.session_id,NEW.video_id) IS DISTINCT FROM
    (OLD.organization_id,OLD.session_id,OLD.video_id) OR NEW.revision <> OLD.revision + 1
 THEN RAISE EXCEPTION 'video review head CAS'; END IF;
 IF (NEW.subject_digest <> OLD.subject_digest OR
     (OLD.payload #>> '{value,applicability}') <> 'effective') AND
    (NEW.payload #>> '{value,applicability}') = 'effective' AND
    (NEW.payload #> '{value,entry}') IS DISTINCT FROM 'null'::jsonb
 THEN RAISE EXCEPTION 'video review cannot copy old approval'; END IF;
 RETURN NEW;
END; $$
"""
PLAYBACK_GUARD = r"""
CREATE FUNCTION video_review.guard_playback() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'video playback delete forbidden'; END IF;
 IF (NEW.organization_id,NEW.session_id,NEW.principal_id,NEW.client_key,NEW.video_id)
    IS DISTINCT FROM
    (OLD.organization_id,OLD.session_id,OLD.principal_id,OLD.client_key,OLD.video_id)
    OR OLD.state <> 'pending' OR OLD.revision <> 1 OR NEW.revision <> 2
    OR NEW.state NOT IN ('playing','rejected')
 THEN RAISE EXCEPTION 'video playback immutable or stale'; END IF;
 RETURN NEW;
END; $$
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA video_review")
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    for definition in (IMMUTABLE, HEAD_GUARD, PLAYBACK_GUARD):
        op.execute(definition)
    for table in ("receipt", "history", "playback_history", "event"):
        op.execute(
            f"CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON video_review.{table} "
            "FOR EACH ROW EXECUTE FUNCTION video_review.immutable_row()"
        )
    op.execute(
        "CREATE TRIGGER guard_head BEFORE UPDATE OR DELETE ON video_review.head "
        "FOR EACH ROW EXECUTE FUNCTION video_review.guard_head()"
    )
    op.execute(
        "CREATE TRIGGER guard_playback BEFORE UPDATE OR DELETE ON video_review.playback "
        "FOR EACH ROW EXECUTE FUNCTION video_review.guard_playback()"
    )


def downgrade() -> None:
    # Only an approved disposable own test database, exact tables, no CASCADE.
    for table in ("event", "playback_history", "playback", "history", "receipt", "head"):
        op.execute(f"DROP TABLE video_review.{table}")
    for function in ("guard_playback", "guard_head", "immutable_row"):
        op.execute(f"DROP FUNCTION video_review.{function}()")
    op.execute("DROP SCHEMA video_review")
