"""DDL-D (T-12b-fix): a controlled lifecycle purge of one managed BE1 profile.

FEAT-066 goal v4 T-12b-fix, owner decision Q5 of 2026-11-23 (SRS l.281 BR-35, l.504 FR-C-10,
l.1065, l.1498 UC-09: deleting a profile purges its dependent content at once). Before this
revision nothing could delete a profile that has revisions: the append-only trigger of
``be1_profile_revisions`` refuses every DELETE, the foreign keys of the revisions, the support
needs and the synthetic eligibility proofs are ``ON DELETE RESTRICT``, and the support-needs
table refuses DELETE as well.

Parent of this revision is ``20261121_psn_0002`` (the head of the BE1 branch, so the revisions,
the support-needs table and their triggers exist). Alembic heads stay 15 down-only (10
dependency-aware); the graph has 56 revisions.

Upgrade, in order:

1. ``reject_be1_profile_revision_change`` is replaced: an UPDATE is still refused; a DELETE is
   refused unless the transaction-local setting ``sketch2life.profile_purge`` equals the
   ``child_id`` of that very row.
2. ``refuse_be1_profile_support_needs_delete`` is replaced the same way.
3. ``public.be1_purge_profile(organization_id, child_id)`` is created. It locks the profile row,
   sets the setting for this transaction only (``set_config(..., true)``), deletes the support
   needs, the synthetic eligibility proofs, the revisions, the command receipts that belong to
   the child and then the profile (its deferred head foreign key is satisfied at commit because
   the profile is gone), clears the setting and returns counts only, never a value. It does not
   commit: the caller owns the transaction, so a failure leaves everything in place.

Scope of the purge, stated plainly. The function removes only: the support-needs row, the
synthetic eligibility proofs, the profile revisions, the command receipts that belong to the child
and the managed profile row. It does NOT purge other tables that carry the child id without a
foreign key: enrollments, consent records, session group memberships and turns, observations and
the admitted-child id of device grants, and it does not decide the retention of audit rows. Those
are open items of the FR-C-10 / BR-35 / UC-09 lifecycle executor (a follow-up task), not done here.
Receipts are found by the child id in their stored answer, by the revision id of an edit, and by
the scope shapes of the edit, move and support-needs commands (the hashed scope form only for the
current class: a receipt under a class the profile has left, with a scope over 256 characters, is
not reachable; it holds ids and a keyed MAC, no value).

The setting is a guard against accident, not an access control: any session may set it. The
function pins ``search_path`` and ``EXECUTE`` is revoked from ``PUBLIC``, so only the owner can
call it. Open item: a role split (a purge role with ``EXECUTE``, an application role without it)
and a trigger guard that no longer trusts a session setting; no role split exists yet.

Downgrade restores the two original function bodies and drops the purge function. It touches no
row, so it needs no guard. Run it with an explicit target, never ``-1``, on a disposable database:
``alembic downgrade 20261121_psn_0002``. Never run against ``sketch2life_m2_s1a`` or ports
5432/5433.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261123_ppg_0001"
down_revision = "20261121_psn_0002"
branch_labels = None
depends_on = None

SETTING = "sketch2life.profile_purge"
REVISION_FUNCTION = "reject_be1_profile_revision_change"
SUPPORT_FUNCTION = "refuse_be1_profile_support_needs_delete"
PURGE_FUNCTION = "be1_purge_profile"

REVISION_FUNCTION_PURGE_SQL = f"""
CREATE OR REPLACE FUNCTION public.{REVISION_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE'
     AND current_setting('{SETTING}', true) IS NOT DISTINCT FROM OLD.child_id THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'BE1_PROFILE_REVISION_IS_APPEND_ONLY'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

REVISION_FUNCTION_ORIGINAL_SQL = f"""
CREATE OR REPLACE FUNCTION public.{REVISION_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'BE1_PROFILE_REVISION_IS_APPEND_ONLY'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

SUPPORT_FUNCTION_PURGE_SQL = f"""
CREATE OR REPLACE FUNCTION public.{SUPPORT_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF current_setting('{SETTING}', true) IS NOT DISTINCT FROM OLD.child_id THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_DELETE_FORBIDDEN'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

SUPPORT_FUNCTION_ORIGINAL_SQL = f"""
CREATE OR REPLACE FUNCTION public.{SUPPORT_FUNCTION}() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'BE1_PROFILE_SUPPORT_NEEDS_DELETE_FORBIDDEN'
    USING ERRCODE = 'integrity_constraint_violation';
END;
$$
"""

PURGE_FUNCTION_SQL = f"""
CREATE FUNCTION public.{PURGE_FUNCTION}(p_organization_id varchar, p_child_id varchar)
RETURNS jsonb
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_class_id varchar;
  v_support integer := 0;
  v_proofs integer := 0;
  v_revisions integer := 0;
  v_receipts integer := 0;
  v_profiles integer := 0;
  v_digest text;
BEGIN
  SELECT p.class_id INTO v_class_id
    FROM public.be1_managed_profiles p
   WHERE p.organization_id = p_organization_id AND p.child_id = p_child_id
     FOR UPDATE;
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'profiles', 0, 'revisions', 0, 'support_needs', 0, 'proofs', 0, 'receipts', 0);
  END IF;
  PERFORM set_config('{SETTING}', p_child_id, true);

  DELETE FROM public.be1_profile_support_needs WHERE child_id = p_child_id;
  GET DIAGNOSTICS v_support = ROW_COUNT;
  DELETE FROM public.be1_synthetic_eligibility_proofs WHERE child_profile_id = p_child_id;
  GET DIAGNOSTICS v_proofs = ROW_COUNT;

  v_digest := encode(
    sha256(convert_to(p_organization_id || '/' || v_class_id || '/' || p_child_id, 'UTF8')),
    'hex');
  DELETE FROM public.be1_command_receipts r
   WHERE r.response_json ->> 'child_id' = p_child_id
      OR r.response_json ->> 'profile_revision_id' IN (
           SELECT x.profile_revision_id FROM public.be1_profile_revisions x
            WHERE x.child_id = p_child_id)
      OR (left(r.operation_scope, length('PATCH /organizations/' || p_organization_id
                                        || '/classes/'))
              = 'PATCH /organizations/' || p_organization_id || '/classes/'
          AND right(r.operation_scope, length('/profiles/' || p_child_id))
              = '/profiles/' || p_child_id)
      OR (left(r.operation_scope, length('POST /classes/')) = 'POST /classes/'
          AND right(r.operation_scope, length('/profiles/' || p_child_id || '/move'))
              = '/profiles/' || p_child_id || '/move')
      OR (left(r.operation_scope, length('PUT /organizations/' || p_organization_id
                                        || '/classes/'))
              = 'PUT /organizations/' || p_organization_id || '/classes/'
          AND right(r.operation_scope,
                    length('/profiles/' || p_child_id || '/support-needs'))
              = '/profiles/' || p_child_id || '/support-needs')
      OR r.operation_scope IN (
           'PATCH /organizations/classes/profiles#' || v_digest,
           'PUT /organizations/classes/profiles/support-needs#' || v_digest,
           'POST /classes/profiles/move#'
             || encode(sha256(convert_to(v_class_id || '/' || p_child_id, 'UTF8')), 'hex'));
  GET DIAGNOSTICS v_receipts = ROW_COUNT;

  DELETE FROM public.be1_profile_revisions WHERE child_id = p_child_id;
  GET DIAGNOSTICS v_revisions = ROW_COUNT;
  DELETE FROM public.be1_managed_profiles
   WHERE organization_id = p_organization_id AND child_id = p_child_id;
  GET DIAGNOSTICS v_profiles = ROW_COUNT;

  PERFORM set_config('{SETTING}', '', true);
  RETURN jsonb_build_object(
    'profiles', v_profiles, 'revisions', v_revisions, 'support_needs', v_support,
    'proofs', v_proofs, 'receipts', v_receipts);
END;
$$
"""


REVOKE_SQL = f"REVOKE ALL ON FUNCTION public.{PURGE_FUNCTION}(varchar, varchar) FROM PUBLIC"


def upgrade() -> None:
    op.execute(sa.text(REVISION_FUNCTION_PURGE_SQL))
    op.execute(sa.text(SUPPORT_FUNCTION_PURGE_SQL))
    op.execute(sa.text(PURGE_FUNCTION_SQL))
    # Only the owner may call it until the purge role exists (open item below).
    op.execute(sa.text(REVOKE_SQL))


def downgrade() -> None:
    op.execute(sa.text(f"DROP FUNCTION public.{PURGE_FUNCTION}(varchar, varchar)"))
    op.execute(sa.text(SUPPORT_FUNCTION_ORIGINAL_SQL))
    op.execute(sa.text(REVISION_FUNCTION_ORIGINAL_SQL))
