"""Metadata-only read composer; no job input, child references or provider payloads."""

from time import perf_counter

from sqlalchemy import func, select

from sketch2life.infrastructure.ai_jobs.sql.tables import attempt, job
from sketch2life.infrastructure.persistence.be1_models import DataLifecycleRequestModel
from sketch2life.infrastructure.persistence.core_models import CoreOutboxEventModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
from sketch2life.infrastructure.platform_admin.pagination import (
    apply_datetime_cursor,
    cursor_scope,
    next_datetime_cursor,
)


class OperationsReader:
    def __init__(self, db, settings=None):
        self.db, self.settings = db, settings

    def _broker_status(self):
        redis_url = self.settings.redis_url if self.settings is not None else None
        if redis_url is None or not redis_url.get_secret_value():
            return {
                "status": "not_configured",
                "response_ms": None,
                "queue_count": None,
                "transport_pending_count": None,
                "active_workers": None,
            }
        client = None
        started = perf_counter()
        try:
            from redis import Redis
            from rq import Queue, Worker

            client = Redis.from_url(
                redis_url.get_secret_value(),
                socket_connect_timeout=0.8,
                socket_timeout=0.8,
            )
            client.ping()
            queues = Queue.all(connection=client)
            return {
                "status": "healthy",
                "response_ms": round((perf_counter() - started) * 1000, 1),
                "queue_count": len(queues),
                "transport_pending_count": sum(queue.count for queue in queues),
                "active_workers": len(Worker.all(connection=client)),
            }
        except Exception:
            # Availability only: never return connection strings or low-level errors.
            return {
                "status": "unavailable",
                "response_ms": round((perf_counter() - started) * 1000, 1),
                "queue_count": None,
                "transport_pending_count": None,
                "active_workers": None,
            }
        finally:
            if client is not None:
                client.close()

    def summary(self):
        database_started = perf_counter()
        self.db.execute(select(1))
        database = {
            "status": "healthy",
            "response_ms": round((perf_counter() - database_started) * 1000, 1),
        }
        jobs = self.db.execute(
            select(job.c.state, job.c.job_type, func.count()).group_by(job.c.state, job.c.job_type)
        ).all()
        queued_count = self.db.scalar(
            select(func.count()).select_from(job).where(job.c.state == "queued")
        ) or 0
        running_count = self.db.scalar(
            select(func.count()).select_from(job).where(job.c.state == "running")
        ) or 0
        failed_count = self.db.scalar(
            select(func.count())
            .select_from(job)
            .where(job.c.state.in_(("failed_retryable", "failed_exhausted", "blocked_unsafe")))
        ) or 0
        oldest_queued = self.db.scalar(
            select(func.min(job.c.created_at)).where(job.c.state == "queued")
        )
        dispatch_times = self.db.execute(
            select(
                func.max(attempt.c.dispatched_at),
                func.max(attempt.c.started_at),
                func.max(attempt.c.finished_at),
            )
        ).one()
        outbox = self.db.execute(
            select(CoreOutboxEventModel.status, func.count()).group_by(CoreOutboxEventModel.status)
        ).all()
        email = self.db.execute(
            select(EmailDeliveryModel.state, func.count()).group_by(EmailDeliveryModel.state)
        ).all()
        lifecycle = self.db.execute(
            select(DataLifecycleRequestModel.state, func.count()).group_by(
                DataLifecycleRequestModel.state
            )
        ).all()
        return {
            "database": database,
            "broker": self._broker_status(),
            "queue": {
                "queued_jobs": queued_count,
                "running_jobs": running_count,
                "failed_jobs": failed_count,
                "oldest_queued_at": oldest_queued.isoformat() if oldest_queued else None,
                "last_dispatched_at": dispatch_times[0].isoformat() if dispatch_times[0] else None,
                "last_started_at": dispatch_times[1].isoformat() if dispatch_times[1] else None,
                "last_finished_at": dispatch_times[2].isoformat() if dispatch_times[2] else None,
            },
            "jobs": [{"state": s, "job_type": t, "count": n} for s, t, n in jobs],
            "core_outbox": [{"state": s, "count": n} for s, n in outbox],
            "email": [{"state": s, "count": n} for s, n in email],
            "lifecycle": [{"state": s, "count": n} for s, n in lifecycle],
        }

    def lifecycle(self, state, organization_id, limit, cursor):
        query = select(DataLifecycleRequestModel)
        if state:
            query = query.where(DataLifecycleRequestModel.state == state)
        if organization_id:
            query = query.where(DataLifecycleRequestModel.organization_id == organization_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("lifecycle", state or "", organization_id or "")
        query = apply_datetime_cursor(
            query,
            created_at_column=DataLifecycleRequestModel.created_at,
            reference_column=DataLifecycleRequestModel.request_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                query.order_by(
                    DataLifecycleRequestModel.created_at.desc(),
                    DataLifecycleRequestModel.request_id,
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.request_id,
        )
        return {
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "request_id": r.request_id,
                    "organization_id": r.organization_id,
                    "request_type": r.request_type,
                    "state": r.state,
                    "unresolved_items": r.unresolved_items,
                    "created_at": r.created_at.isoformat(),
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in rows[:limit]
            ],
        }

    def email_deliveries(self, state, limit, cursor):
        query = select(EmailDeliveryModel)
        if state:
            query = query.where(EmailDeliveryModel.state == state)
        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        scope = cursor_scope("email-deliveries", state or "")
        query = apply_datetime_cursor(
            query,
            created_at_column=EmailDeliveryModel.created_at,
            reference_column=EmailDeliveryModel.delivery_id,
            scope=scope,
            cursor=cursor,
            dialect=self.db.get_bind().dialect.name,
        )
        rows = list(
            self.db.scalars(
                query.order_by(
                    EmailDeliveryModel.created_at.desc(), EmailDeliveryModel.delivery_id
                ).limit(limit + 1)
            )
        )
        next_cursor = next_datetime_cursor(
            rows,
            limit,
            scope=scope,
            created_at=lambda row: row.created_at,
            reference=lambda row: row.delivery_id,
        )
        return {
            "total": total,
            "limit": limit,
            "next_cursor": next_cursor,
            "items": [
                {
                    "delivery_id": r.delivery_id,
                    "template": r.template,
                    "state": r.state,
                    "attempts": r.attempts,
                    "failure_code": r.failure_code,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows[:limit]
            ],
        }
