export type LiveUnderstandingResponse = Readonly<{
  status: 'PROPOSAL' | 'FAILED';
  proposal_label: string | null;
  gate_a_required: boolean;
  request_id: string;
}>;

type LiveUnderstandingRequest = Readonly<{
  baseUrl: string;
  sessionId: string;
  expectedSessionVersion: number;
  fixtureId: string;
}>;

export async function requestLiveUnderstanding({
  baseUrl,
  sessionId,
  expectedSessionVersion,
  fixtureId,
}: LiveUnderstandingRequest): Promise<LiveUnderstandingResponse> {
  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/v1/live-understanding`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', Accept: 'application/json'},
    body: JSON.stringify({
      mode: 'live-lightning',
      fixture_id: fixtureId,
      session_id: sessionId,
      expected_session_version: expectedSessionVersion,
    }),
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    throw new Error(`Live backend request failed (${response.status})`);
  }
  if (!isLiveUnderstandingResponse(body)) {
    throw new Error('Live backend returned an invalid understanding contract');
  }
  if (body.status === 'FAILED') {
    throw new Error('Live backend could not produce a validated proposal');
  }
  if (!body.gate_a_required) {
    throw new Error('Live backend returned a proposal without Gate A');
  }
  return body;
}

function isLiveUnderstandingResponse(value: unknown): value is LiveUnderstandingResponse {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    (candidate.status === 'PROPOSAL' || candidate.status === 'FAILED') &&
    (candidate.proposal_label === null || typeof candidate.proposal_label === 'string') &&
    typeof candidate.gate_a_required === 'boolean' &&
    typeof candidate.request_id === 'string'
  );
}
