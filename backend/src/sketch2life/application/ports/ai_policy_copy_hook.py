"""BE2-14 internal hook contract; actual BE2-04/08 adoption remains separate."""

from typing import Protocol

from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.contracts.schemas.ai_policy_copy_operation import CopyOperationEnvelope


class ProviderCopyOperationHook(Protocol):
    def dispatch(self, envelope: CopyOperationEnvelope) -> CopyHookResponse:
        """Execute only after current authority+original profile and persisted claim.

        Caller holds no DB transaction while invoking the hook. Hook uses ORIGINAL
        exact profile and stable operation_key as external dedup key, never latest
        alias or new key on restart/timeout. Same key/different body must conflict.
        Return reference/hash for later authoritative verification; accepted/sent
        does NOT mean cancelled/deleted. No actual hook/default implementation.
        """
        ...
