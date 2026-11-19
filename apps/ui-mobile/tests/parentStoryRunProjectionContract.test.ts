import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort, ParentActionIdentity } from '../src/parent/application/ports/ParentPorts';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';
import type {
  ParentActiveStoryRunEnvelopeV1,
  ParentDrawingCandidateDecisionV1,
  ParentDrawingCandidateV1,
  ParentLessonPinSnapshotV1,
  ParentStoryContextV1,
  ParentStoryDisplayV1,
  ParentStoryJobStateV1,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunStateV1,
  ParentStoryRunV1,
  ParentStoryStatusV1,
  ParentStorySubjectConfirmationV1,
} from '../src/parent/domain/types';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

type ProjectionProperty = {
  const?: string;
  enum?: string[];
  anyOf?: ProjectionProperty[];
};

type ProjectionSchema = {
  properties?: Record<string, ProjectionProperty>;
  required?: string[];
};

type ProjectionOperation = {
  parameters?: Array<{ in: string; name: string; required?: boolean }>;
  security?: Array<Record<string, string[]>>;
};

type ProjectionSecurityScheme = { type: string; scheme?: string };

type ProjectionDocument = {
  components: {
    schemas: Record<string, ProjectionSchema>;
    securitySchemes: Record<string, ProjectionSecurityScheme>;
  };
  paths: Record<string, Record<string, ProjectionOperation>>;
  security?: Array<Record<string, string[]>>;
};

const projection = JSON.parse(readFileSync(new URL(
  '../../../features/FEAT-063-system-architecture-rearchitecture/artifacts/m2-s3/openapi-client-projection-frozen.json',
  import.meta.url,
), 'utf8')) as ProjectionDocument;

const parentStoryRunRequiredKeys = [
  'run_id',
  'run_revision',
  'run_state',
  'parent_profile_id',
  'profile_revision_ref',
  'context_revision',
  'context_confirmed',
  'context_snapshot',
  'context_snapshot_sha256',
  'current_input_revision',
  'understanding_revision',
  'subject_label',
  'candidate',
  'story_revision_id',
  'story_revision_no',
  'story_status',
  'story_sha256',
  'story',
  'job_state',
  'retryable',
  'error_code',
  'created_at',
  'updated_at',
] as const satisfies readonly (keyof ParentStoryRunV1)[];

const parentStoryRunEnvelopeRequiredKeys = ['request_id', 'story_run'] as const satisfies readonly (keyof ParentStoryRunEnvelopeV1)[];
const parentActiveStoryRunEnvelopeRequiredKeys = ['request_id', 'story_run'] as const satisfies readonly (keyof ParentActiveStoryRunEnvelopeV1)[];
const parentStoryContextRequiredKeys = [
  'schema_version',
  'profile_revision_ref',
  'age_months',
  'interests_summary',
  'topic',
  'adult_confirmed_idea',
] as const satisfies readonly (keyof ParentStoryContextV1)[];
const parentLessonPinRequiredKeys = [
  'schema_version',
  'lesson_id',
  'version_id',
  'version_no',
  'content_sha256',
  'title',
  'topic',
  'drawing_subject',
  'subject_learning_notes',
  'script_following_allowed',
  'activities',
] as const satisfies readonly (keyof ParentLessonPinSnapshotV1)[];
const parentDrawingCandidateRequiredKeys = [
  'candidate_subject',
  'visible_features',
  'confidence',
  'adult_confirmation_required',
  'decision',
] as const satisfies readonly (keyof ParentDrawingCandidateV1)[];
const parentStoryDisplayRequiredKeys = [
  'schema_version',
  'language',
  'title',
  'story',
  'duration_ms',
  'scenes',
] as const satisfies readonly (keyof ParentStoryDisplayV1)[];
const parentSubjectConfirmationRequiredKeys = [
  'request_id',
  'story_run_id',
  'understanding_revision',
  'decision',
] as const satisfies readonly (keyof ParentStorySubjectConfirmationV1)[];

const parentStoryRunStates = [
  'INPUT_PROCESSING',
  'SUBJECT_REVIEW',
  'PREPARATION_REVIEW',
  'SCRIPT_GENERATING',
  'SCRIPT_GENERATION_UNKNOWN',
  'SCRIPT_REVIEW',
  'VIDEO_ADMISSION_PENDING',
  'DELETE_PENDING',
  'FAILED',
  'COMPLETED',
] as const;
const parentStoryStatuses = [
  'GENERATING',
  'DRAFT',
  'CONFIRMED',
  'SUPERSEDED',
  'FAILED',
  'AWAITING_RECONCILIATION',
] as const;
const parentStoryJobStates = [
  'QUEUED',
  'RUNNING',
  'SUCCEEDED',
  'FAILED',
  'AWAITING_RECONCILIATION',
] as const;
const parentDrawingCandidateDecisions = [
  'REVIEW_REQUIRED',
  'CONFIRMED_BY_ADULT',
  'CORRECTED_BY_ADULT',
] as const;

type RequiredKeys<T> = {
  [Key in keyof T]-?: {} extends Pick<T, Key> ? never : Key;
}[keyof T];
type Equal<Left, Right> = [Left] extends [Right]
  ? [Right] extends [Left] ? true : false
  : false;
type Assert<Condition extends true> = Condition;

const compileTimeParity: [
  Assert<Equal<RequiredKeys<ParentStoryRunV1>, (typeof parentStoryRunRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentStoryRunEnvelopeV1>, (typeof parentStoryRunEnvelopeRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentActiveStoryRunEnvelopeV1>, (typeof parentActiveStoryRunEnvelopeRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentStoryContextV1>, (typeof parentStoryContextRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentLessonPinSnapshotV1>, (typeof parentLessonPinRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentDrawingCandidateV1>, (typeof parentDrawingCandidateRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentStoryDisplayV1>, (typeof parentStoryDisplayRequiredKeys)[number]>>,
  Assert<Equal<RequiredKeys<ParentStorySubjectConfirmationV1>, (typeof parentSubjectConfirmationRequiredKeys)[number]>>,
  Assert<Equal<ParentStoryRunStateV1, (typeof parentStoryRunStates)[number]>>,
  Assert<Equal<ParentStoryStatusV1, (typeof parentStoryStatuses)[number]>>,
  Assert<Equal<ParentStoryJobStateV1, (typeof parentStoryJobStates)[number]>>,
  Assert<Equal<ParentDrawingCandidateDecisionV1, (typeof parentDrawingCandidateDecisions)[number]>>,
  Assert<Equal<ParentStoryContextV1['schema_version'], 'sketch2life.parent-context.v1'>>,
  Assert<Equal<ParentLessonPinSnapshotV1['schema_version'], 'sketch2life.parent-lesson-pin.v1'>>,
  Assert<Equal<ParentStoryDisplayV1['language'], 'vi'>>,
  Assert<Equal<ParentStorySubjectConfirmationV1['decision'], 'CONFIRMED'>>,
] = [true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true];
void compileTimeParity;

type ApiRouteCase = {
  name: string;
  pathTemplate: string;
  method: 'get' | 'post' | 'patch' | 'delete';
  invoke(api: ParentApi): Promise<unknown>;
};

const actionIdentity = 'projection-contract-action' as ParentActionIdentity;
const profileInput = { display_name: 'Synthetic profile', age_months: 72, interests_summary: null };
const storyRunInput = {
  parent_profile_id: 'synthetic-profile',
  topic: 'Synthetic topic',
  adult_confirmed_idea: 'Synthetic adult idea',
};
const apiRouteCases: ApiRouteCase[] = [
  {
    name: 'listProfilesV1',
    pathTemplate: '/v1/parent/profiles',
    method: 'get',
    invoke: (api) => api.listProfilesV1(),
  },
  {
    name: 'getProfileV1',
    pathTemplate: '/v1/parent/profiles/{profile_id}',
    method: 'get',
    invoke: (api) => api.getProfileV1('synthetic-profile'),
  },
  {
    name: 'createProfileV1',
    pathTemplate: '/v1/parent/profiles',
    method: 'post',
    invoke: (api) => api.createProfileV1(profileInput, actionIdentity),
  },
  {
    name: 'patchProfileV1',
    pathTemplate: '/v1/parent/profiles/{profile_id}',
    method: 'patch',
    invoke: (api) => api.patchProfileV1('synthetic-profile', {
      expected_revision: 1,
      display_name: 'Synthetic profile',
      age_months: 72,
    }, actionIdentity),
  },
  {
    name: 'requestProfileDeletionV1',
    pathTemplate: '/v1/parent/profiles/{profile_id}',
    method: 'delete',
    invoke: (api) => api.requestProfileDeletionV1('synthetic-profile', actionIdentity),
  },
  {
    name: 'getActiveStoryRunV1',
    pathTemplate: '/v1/story-runs/active/current',
    method: 'get',
    invoke: (api) => api.getActiveStoryRunV1(),
  },
  {
    name: 'getStoryRunV1',
    pathTemplate: '/v1/story-runs/{run_id}',
    method: 'get',
    invoke: (api) => api.getStoryRunV1('synthetic-run'),
  },
  {
    name: 'createStoryRunV1',
    pathTemplate: '/v1/story-runs',
    method: 'post',
    invoke: (api) => api.createStoryRunV1(storyRunInput, actionIdentity),
  },
  {
    name: 'confirmStoryRunContextV1',
    pathTemplate: '/v1/story-runs/{run_id}/context-confirmation',
    method: 'post',
    invoke: (api) => api.confirmStoryRunContextV1('synthetic-run', {
      expected_context_revision: 1,
      context_snapshot_sha256: 'a'.repeat(64),
      confirmed: true,
    }, actionIdentity),
  },
  {
    name: 'confirmStoryRunSubjectV1',
    pathTemplate: '/v1/story-runs/{run_id}/subject-confirmation',
    method: 'post',
    invoke: (api) => api.confirmStoryRunSubjectV1('synthetic-run', 1, 'Synthetic subject', actionIdentity),
  },
  {
    name: 'confirmStoryRunScriptV1',
    pathTemplate: '/v1/story-runs/{run_id}/script-confirmation',
    method: 'post',
    invoke: (api) => api.confirmStoryRunScriptV1('synthetic-run', 1, 'b'.repeat(64), actionIdentity),
  },
];

function projectedEnum(schemaName: string, propertyName: string): string[] {
  const property = projection.components.schemas[schemaName]?.properties?.[propertyName];
  if (property?.enum) return property.enum;
  return property?.anyOf?.find((item) => item.enum)?.enum ?? [];
}

function projectedRequiredHeaders(operation: ProjectionOperation): string[] {
  const parameterHeaders = (operation.parameters ?? [])
    .filter((parameter) => parameter.in === 'header' && parameter.required)
    .map((parameter) => parameter.name);
  const security = operation.security ?? projection.security ?? [];
  const bearerRequired = security.some((requirement) => Object.keys(requirement).some((schemeName) => {
    const scheme = projection.components.securitySchemes[schemeName];
    return scheme?.type === 'http' && scheme.scheme === 'bearer';
  }));
  return [...new Set([...parameterHeaders, ...(bearerRequired ? ['Authorization'] : [])])];
}

function matchesPathTemplate(actualPath: string, pathTemplate: string): boolean {
  const actualSegments = actualPath.split('/');
  const templateSegments = pathTemplate.split('/');
  if (actualSegments.length !== templateSegments.length) return false;
  return templateSegments.every((segment, index) => {
    if (segment.startsWith('{') && segment.endsWith('}')) return actualSegments[index].length > 0;
    return actualSegments[index] === segment;
  });
}

describe('Parent story-run frozen projection contract', () => {
  it('keeps required fields and enums aligned with the frozen schemas', () => {
    const requiredSchemaCases = [
      { schemaName: 'ParentStoryRunResponseV1', keys: parentStoryRunRequiredKeys },
      { schemaName: 'ParentStoryRunEnvelopeV1', keys: parentStoryRunEnvelopeRequiredKeys },
      { schemaName: 'ParentActiveStoryRunEnvelopeV1', keys: parentActiveStoryRunEnvelopeRequiredKeys },
      { schemaName: 'ParentRunContextSnapshotV1', keys: parentStoryContextRequiredKeys },
      { schemaName: 'ParentLessonPinSnapshotV1', keys: parentLessonPinRequiredKeys },
      { schemaName: 'ParentDrawingCandidateV1', keys: parentDrawingCandidateRequiredKeys },
      { schemaName: 'ParentStoryDisplayV1', keys: parentStoryDisplayRequiredKeys },
      { schemaName: 'ParentSubjectConfirmationResponseV1', keys: parentSubjectConfirmationRequiredKeys },
    ];

    for (const contract of requiredSchemaCases) {
      const projectedRequired = projection.components.schemas[contract.schemaName]?.required ?? [];
      expect([...projectedRequired].sort()).toEqual([...contract.keys].sort());
    }

    const enumCases = [
      { schemaName: 'ParentStoryRunResponseV1', propertyName: 'run_state', values: parentStoryRunStates },
      { schemaName: 'ParentStoryRunResponseV1', propertyName: 'story_status', values: parentStoryStatuses },
      { schemaName: 'ParentStoryRunResponseV1', propertyName: 'job_state', values: parentStoryJobStates },
      { schemaName: 'ParentDrawingCandidateV1', propertyName: 'decision', values: parentDrawingCandidateDecisions },
    ];

    for (const contract of enumCases) {
      expect([...projectedEnum(contract.schemaName, contract.propertyName)].sort()).toEqual([...contract.values].sort());
    }

    expect(projection.components.schemas.ParentRunContextSnapshotV1.properties?.schema_version?.const)
      .toBe('sketch2life.parent-context.v1');
    expect(projection.components.schemas.ParentLessonPinSnapshotV1.properties?.schema_version?.const)
      .toBe('sketch2life.parent-lesson-pin.v1');
    expect(projection.components.schemas.ParentStoryDisplayV1.properties?.language?.const).toBe('vi');
    expect(projection.components.schemas.ParentSubjectConfirmationResponseV1.properties?.decision?.const)
      .toBe('CONFIRMED');
  });

  it('calls all 11 projected Parent methods with their required headers', async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'synthetic-token') };
    const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      return {
        ok: true,
        status: 200,
        headers: new Headers(),
        json: async () => ({}),
      } as Response;
    }) as unknown as typeof fetch;
    const api = new ParentApi(auth, fetcher, 'https://api.example.test');

    for (const route of apiRouteCases) {
      const operation = projection.paths[route.pathTemplate]?.[route.method];
      expect(operation).toBeDefined();
      await route.invoke(api);

      const call = calls[calls.length - 1];
      expect(call.init.method?.toLowerCase()).toBe(route.method);
      expect(matchesPathTemplate(new URL(call.url).pathname, route.pathTemplate)).toBe(true);
      const headers = new Headers(call.init.headers);
      for (const requiredHeader of projectedRequiredHeaders(operation!)) {
        expect(headers.has(requiredHeader)).toBe(true);
      }
    }

    expect(calls).toHaveLength(11);
  });
});
