import base64, hashlib, json, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from pydantic import TypeAdapter, ValidationError
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2, VisionUnderstandingResultV2,
    VisionUnderstandingSuccessV2, vision_profile_catalog_v2,
    vision_profile_catalog_hash_v2, vision_profile_config_hash_v2,
)

folder = Path(__file__).resolve().parent
root = folder.parents[3]
payload = json.loads((folder / 'request.json').read_bytes())
source = (folder / 'synthetic-house-sun.png').read_bytes()
admission = (folder / 'admission.json').read_bytes()
template = VisionUnderstandingRequestV2.model_validate(payload['request'])
if template.source_image_ref.sha256 != hashlib.sha256(source).hexdigest():
    raise SystemExit('STOP: source digest mismatch')
if base64.b64decode(payload['source_image']['content_base64'], validate=True) != source:
    raise SystemExit('STOP: encoded source mismatch')
if template.media_validation is None or template.media_validation.decision != 'PASS':
    raise SystemExit('STOP: missing admission')
if template.media_validation.validation_artifact_sha256 != hashlib.sha256(admission).hexdigest():
    raise SystemExit('STOP: admission digest mismatch')
if json.loads(admission)['receipt']['decision'] != 'ADMITTED':
    raise SystemExit('STOP: image was not admitted')
secret = sys.stdin.readline().rstrip('\r\n')
if len(secret) < 32:
    raise SystemExit('STOP: saved secret unavailable')
catalog = vision_profile_catalog_v2()
profile = catalog.resolve(template.requested_profile_id)
adapter = TypeAdapter(VisionUnderstandingResultV2)
serve_url = sys.argv[1] if len(sys.argv) == 2 else '<MODAL_SERVE_URL>'
if serve_url.startswith('<'):
    raise SystemExit('STOP: set serve_url to the current modal serve URL')
url = serve_url.rstrip('/') + '/v2/vision'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
report_path = folder / ('inference-metrics-' + stamp + '.jsonl')
fields = {
    'contract_name', 'contract_version', 'correlation_id', 'executed_at',
    'source_image_ref', 'profile_id', 'profile_catalog_hash', 'status',
    'attempt_number', 'repair_attempted', 'content_policy_version',
    'policy_match_view_version', 'policy_execution_state', 'adapter_version',
    'config_hash', 'error_code', 'error_detail', 'retryable', 'mapping_diagnostics',
}
class SmokeCheckError(Exception):
    pass

exit_code = 0
with report_path.open('x', encoding='utf-8') as report:
    report.write(json.dumps({
        'max_calls': 2, 'client_timeout_seconds': 150,
        'gpu_peak_memory': 'NOT_MEASURED', 'billed_duration': 'NOT_MEASURED',
        'timing_kind': 'client_wall_seconds', 'warm_container_identity': 'NOT_VERIFIED',
    }, sort_keys=True) + '\n')
    report.flush()
    for phase in ('first_request', 'immediate_followup'):
        correlation = 'modal-smoke-house-sun-v1-' + phase
        payload['request']['correlation_id'] = correlation
        wire = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        request = urllib.request.Request(
            url, data=wire, method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + secret},
        )
        http_status = None
        started_at = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=150) as response:
                http_status = response.status
                raw = response.read()
            if http_status != 200:
                raise SmokeCheckError('UNEXPECTED_HTTP_STATUS')
            result = adapter.validate_json(raw)
            if result.correlation_id != correlation or result.source_image_ref != template.source_image_ref:
                raise SmokeCheckError('SOURCE_OR_CORRELATION_MISMATCH')
            if result.profile_id != profile.profile_id or result.profile_catalog_hash != vision_profile_catalog_hash_v2(catalog):
                raise SmokeCheckError('PROFILE_MISMATCH')
            row = result.model_dump(mode='json', include=fields)
            if result.model_provenance is not None:
                row['model_identifier'] = result.model_provenance.model_identifier
                row['model_revision'] = result.model_provenance.model_revision
            if isinstance(result, VisionUnderstandingSuccessV2):
                if result.model_provenance != profile.model_provenance or result.config_hash != vision_profile_config_hash_v2(profile):
                    raise SmokeCheckError('MODEL_OR_CONFIG_MISMATCH')
                if result.adapter_version != profile.adapter_version or result.attempt_number != 1:
                    raise SmokeCheckError('ADAPTER_OR_ATTEMPT_MISMATCH')
                for name in ('entities', 'actions', 'relations', 'themes', 'ambiguous_regions'):
                    row[name + '_count'] = len(getattr(result, name))
        except urllib.error.HTTPError as exc:
            http_status = exc.code
            row = {'status': 'HTTP_ERROR', 'error_type': type(exc).__name__}
            exc.close()
        except SmokeCheckError as exc:
            row = {'status': 'CHECK_FAILED', 'check': str(exc)}
        except ValidationError:
            row = {'status': 'RESPONSE_SCHEMA_INVALID'}
        except Exception as exc:
            row = {'status': 'CLIENT_ERROR', 'error_type': type(exc).__name__}
        row.update(phase=phase, http_status=http_status, started_at_utc=started_at,
                   client_wall_seconds=round(time.perf_counter() - started, 3))
        safe = json.dumps(row, sort_keys=True)
        report.write(safe + '\n')
        report.flush()
        print(safe, flush=True)
        if row.get('status') != 'SUCCEEDED':
            exit_code = 1
            print('STOPPED: no followup and no retry.', flush=True)
            break
print('REPORT: ' + report_path.relative_to(root).as_posix())
sys.exit(exit_code)