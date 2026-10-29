"""Own11 metadata; no FK or SQL writes to12/BE1/foundation."""

from sqlalchemy import BigInteger, CheckConstraint, Column, MetaData, String, Table
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA = "activity_execution"
METADATA = MetaData(schema=SCHEMA)


def table(name: str, keys: tuple[str, ...], *, revision_key: bool = False) -> Table:
    return Table(
        name,
        METADATA,
        *(Column(key, String(120), primary_key=True) for key in keys),
        Column("revision", BigInteger, primary_key=revision_key, nullable=False),
        Column("payload", JSONB, nullable=False),
        CheckConstraint("revision > 0", name=name + "_revision"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name=name + "_object"),
    )


HEAD = table("assignment", ("organization_id", "session_id", "assignment_id"))
HISTORY = table("history", ("organization_id", "session_id", "assignment_id"), revision_key=True)
RECEIPT = table("receipt", ("organization_id", "session_id", "principal_id", "client_key"))
EVENT = table("event", ("organization_id", "session_id", "event_id"))
ACK = table("ack", ("organization_id", "session_id", "event_id"))
