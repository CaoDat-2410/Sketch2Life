"""Guarded intent-first Teacher dispositions; no default real adopters."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from sketch2life.application.ports.video_failure import (
    FailureAccess,
    FailureBoundary,
    FailureBridge,
    FailureStore,
)
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_failure.model import Action, Choice, Context, Intent, request_digest


class VideoFailureService:
    def __init__(
        self,
        boundary: FailureBoundary,
        store: FailureStore,
        bridge: FailureBridge,
        *,
        clock: Callable[[], datetime],
        disposition_ids: Callable[[], str],
    ) -> None:
        self.boundary, self.store, self.bridge = boundary, store, bridge
        self.clock, self.ids = clock, disposition_ids

    def decide(self, context: Context, choice: Choice) -> Intent:
        context, choice = replace(context), replace(choice)
        try:
            with self.boundary.guard(context) as access:
                with self.store.transaction(context.organization_id, context.session_id) as tx:
                    previous = tx.get(context.principal_id, context.client_key)
                if previous is not None:
                    previous = replace(previous)
                    if previous.context != context or previous.digest() != request_digest(
                        context, choice
                    ):
                        raise VideoError("VIDEO_DISPOSITION_IDEMPOTENCY_CONFLICT")
                    access.check(previous, "recover")
                    if previous.receipt is not None:
                        return previous
                    try:
                        receipt = self.bridge.lookup(previous)
                    except Exception:
                        return previous
                    return previous if receipt is None else self._record(access, previous, receipt)
                target = replace(access.resolve(context, choice))
                auth = (
                    access.authorize_retry(context, target)
                    if choice.action is Action.RETRY
                    else None
                )
                intent = Intent(self.ids(), context, choice, target, self.clock(), auth)
                access.check(intent, "prepare")
                # No external effect if insert/commit ACK is uncertain. Fail503;
                # original key may recover a committed intent on a later request.
                with self.store.transaction(context.organization_id, context.session_id) as tx:
                    access.check(intent, "commit_intent")
                    tx.insert(intent)
                    access.check(intent, "commit_intent")
                access.check(intent, "dispatch")
                try:
                    receipt = self.bridge.execute(intent)
                except Exception:
                    return intent
                return self._record(access, intent, receipt)
        except VideoError:
            raise
        except Exception:
            # May follow successful commit/effect. Never claim rollback or revoke.
            raise VideoError("VIDEO_DISPOSITION_DEPENDENCY_UNAVAILABLE") from None

    def _record(self, access: FailureAccess, intent: Intent, receipt: object) -> Intent:
        from sketch2life.domain.video_failure.model import EffectReceipt

        try:
            if type(receipt) is not EffectReceipt:
                return intent
            settled = intent.settle(receipt)
            access.check(intent, "record_receipt")
            c = intent.context
            with self.store.transaction(c.organization_id, c.session_id) as tx:
                current = tx.get(c.principal_id, c.client_key)
                if current is None:
                    raise VideoError("VIDEO_DISPOSITION_INTENT_MISSING")
                current = replace(current)
                if current != intent:
                    if current != settled:
                        raise VideoError("VIDEO_DISPOSITION_STALE_INTENT")
                else:
                    tx.save(settled, expected_revision=intent.revision)
                access.check(intent, "record_receipt")
            return settled
        except Exception:
            # Outcome may exist externally; original key recovers, no repeated effect.
            return intent
