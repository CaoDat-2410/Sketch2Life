import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

import { ParentLearningUseCases } from '../src/parent/application/use-cases/ParentLearningUseCases';
import type { ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import {
  filterSafeSvgGuideCatalogItems,
  isSafeSvgGuideCatalogItem,
  svgGuideCatalogAttribution,
  type SvgGuideCatalogItemV1,
} from '../src/parent/domain/svgGuide';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { parentSvgCatalogFailureMessage } from '../src/parent/presentation/navigation/parentFlowV1';

function catalogItem(): SvgGuideCatalogItemV1 {
  const sourceSha = 'a'.repeat(64);
  return {
    contract: 'SvgGuideCatalogItemV1',
    catalog_entry_id: 'catalog-entry-1',
    guide_revision_id: 'guide-revision-1',
    topic_key: 'sea-creatures',
    title_vi: 'Con cá nhỏ',
    alt_text_vi: 'Hình vẽ con cá nhỏ',
    source_uri: 'https://assets.example.test/fish.svg',
    license_id: 'CC0-1.0',
    license_uri: 'https://assets.example.test/license',
    source_sha256: sourceSha,
    guide_sha256: 'b'.repeat(64),
    document: {
      schema_version: 'SvgDocumentV1',
      view_box: '0 0 100 100',
      paths: [1, 2, 3, 4].map((index) => ({
        path_id: `path-${index}`,
        d: `M0 0 L${index} 4`,
        fill: 'none',
        stroke: '#000000',
        stroke_width: 2,
      })),
    },
    guide: {
      schema_version: 'SketchStrokeGuideV3',
      guide_id: 'guide-1',
      title_vi: 'Con cá nhỏ',
      source_asset_ref: 'asset:catalog-entry-1',
      source_asset_version: 2,
      source_sha256: sourceSha,
      parts: [{
        part_id: 'fish-outline',
        label_vi: 'Thân cá',
        path_ids: ['path-1', 'path-2', 'path-3', 'path-4'],
        depends_on: [],
      }],
      stages: [1, 2, 3, 4].map((stepIndex) => ({
        step_index: stepIndex,
        instruction_vi: `Vẽ nét ${stepIndex}`,
        part_ids: ['fish-outline'],
        new_path_ids: [`path-${stepIndex}`],
        animation_order: [`path-${stepIndex}`],
      })),
    },
  };
}

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(),
    json: async () => body,
  } as unknown as Response;
}

function apiWith(status: number, body: unknown) {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return reply(status, body);
  }) as unknown as typeof fetch;
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, calls };
}

describe('GAP-09 Parent SVG guide catalog', () => {
  it('requests a topic and limit with bearer auth, no cursor, and accepts an empty list', async () => {
    const { api, calls } = apiWith(200, { contract: 'SvgGuideCatalogPageV1', items: [] });
    const page = await api.listSvgCatalogGuides('sea-creatures', 8);
    const url = new URL(calls[0].url);

    expect(page.items).toEqual([]);
    expect(url.pathname).toBe('/api/svg-catalog/v1/parent/guides');
    expect(Object.fromEntries(url.searchParams)).toEqual({ topic_key: 'sea-creatures', limit: '8' });
    expect(new Headers(calls[0].init.headers).get('Authorization')).toBe('Bearer parent-token');
    expect(calls[0].init.method).toBe('GET');
    expect(calls[0].init.body).toBeUndefined();
  });

  it('accepts a validated catalog item from the API page', async () => {
    const item = catalogItem();
    const { api } = apiWith(200, { contract: 'SvgGuideCatalogPageV1', items: [item] });
    await expect(api.listSvgCatalogGuides('sea-creatures')).resolves.toMatchObject({ items: [item] });
  });

  it('drops invalid items individually and reports only an all-invalid page', async () => {
    const valid = catalogItem();
    const invalid = { ...valid, title_vi: '<unsafe>' };
    expect(filterSafeSvgGuideCatalogItems([invalid, valid])).toEqual([valid]);

    const mixed = apiWith(200, { contract: 'SvgGuideCatalogPageV1', items: [invalid, valid] });
    await expect(mixed.api.listSvgCatalogGuides()).resolves.toMatchObject({ items: [valid] });

    const allInvalid = apiWith(200, { contract: 'SvgGuideCatalogPageV1', items: [invalid] });
    const error = await allInvalid.api.listSvgCatalogGuides().catch((cause: unknown) => cause);
    expect(error).toMatchObject({ code: 'PARENT_SVG_GUIDE_INVALID', status: 200 });
    expect(parentSvgCatalogFailureMessage(error)).toBe(
      'Một số hướng dẫn có sẵn không thể hiển thị an toàn. Bạn vẫn có thể tiếp tục.',
    );
  });

  it('omits the unknown taxonomy filter when requested and defaults to 50', async () => {
    const { api, calls } = apiWith(200, { contract: 'SvgGuideCatalogPageV1', items: [] });
    await api.listSvgCatalogGuides();
    const url = new URL(calls[0].url);
    expect(url.searchParams.get('limit')).toBe('50');
    expect(url.searchParams.has('topic_key')).toBe(false);
    expect(url.searchParams.has('cursor')).toBe(false);
  });

  it('maps both error envelopes to calm 403 and 503 copy', async () => {
    const denied = apiWith(403, { detail: { code: 'FORBIDDEN', message: 'private detail' } });
    const deniedError = await denied.api.listSvgCatalogGuides().catch((error: unknown) => error);
    expect(deniedError).toBeInstanceOf(ParentApiError);
    expect(deniedError).toMatchObject({ code: 'FORBIDDEN', status: 403 });
    expect(parentSvgCatalogFailureMessage(deniedError)).toContain('tài khoản này');

    const unavailable = apiWith(503, { code: 'DEPENDENCY_UNAVAILABLE', message: 'private detail' });
    const unavailableError = await unavailable.api.listSvgCatalogGuides().catch((error: unknown) => error);
    expect(unavailableError).toMatchObject({ code: 'DEPENDENCY_UNAVAILABLE', status: 503 });
    expect(parentSvgCatalogFailureMessage(unavailableError)).toContain('tạm thời không sẵn sàng');
  });

  it('accepts a safe catalog item and rejects wrong contracts, unknown paths, short guides, and HTTP sources', () => {
    const good = catalogItem();
    expect(isSafeSvgGuideCatalogItem(good)).toBe(true);
    expect(isSafeSvgGuideCatalogItem({ ...good, contract: 'Other' })).toBe(false);
    expect(isSafeSvgGuideCatalogItem({ ...good, title_vi: '<b>unsafe</b>' })).toBe(false);

    const unknownPath = {
      ...good,
      guide: {
        ...good.guide,
        stages: good.guide.stages.map((stage, index) => index === 0
          ? { ...stage, new_path_ids: ['missing-path'] }
          : stage),
      },
    };
    expect(isSafeSvgGuideCatalogItem(unknownPath)).toBe(false);
    expect(isSafeSvgGuideCatalogItem({ ...good, guide: { ...good.guide, stages: good.guide.stages.slice(0, 3) } })).toBe(false);
    expect(isSafeSvgGuideCatalogItem({ ...good, source_uri: 'http://assets.example.test/fish.svg' })).toBe(false);
  });

  it('uses source host and license as catalog attribution without draft language', () => {
    const attribution = svgGuideCatalogAttribution(catalogItem());
    expect(attribution).toContain('assets.example.test');
    expect(attribution).toContain('CC0-1.0');
    expect(attribution.toLowerCase()).not.toMatch(/draft|bản nháp|duyệt/);

    const screen = readFileSync(new URL('../src/parent/presentation/screens/SketchGuideScreen.tsx', import.meta.url), 'utf8');
    const catalogBranch = screen.slice(
      screen.indexOf('{validCatalogGuide && catalogStage'),
      screen.indexOf('{!validCatalogGuide && validDraft'),
    );
    expect(catalogBranch).toContain('svgGuideCatalogAttribution');
    expect(catalogBranch.toLowerCase()).not.toMatch(/bản nháp|duyệt bản nháp/);
  });

  it('keeps catalog rows and picker subtitle free of backend slugs and draft copy', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/SketchGuideScreen.tsx', import.meta.url), 'utf8');
    const row = screen.slice(
      screen.indexOf('props.catalogGuides.map((guide) => {'),
      screen.indexOf('{props.canCreateGuide ? <Text'),
    );
    expect(row).toContain('guide.title_vi');
    expect(row).toContain('guide.alt_text_vi');
    expect(row).toContain('guide.guide.stages.length');
    expect(row).not.toContain('topic_key');

    const subtitle = screen.slice(screen.indexOf('subtitle={validCatalogGuide'), screen.indexOf('step="Tùy chọn"'));
    expect(subtitle).toContain('props.catalogGuidePickerOpen');
    expect(subtitle).toContain('Hướng dẫn có sẵn.');
    expect(subtitle.toLowerCase()).toContain('bản nháp riêng tư');
    expect(subtitle).toContain('!validDraft');
  });

  it('keeps the AI guide button visible on empty or failed catalog states and tap-only', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/SketchGuideScreen.tsx', import.meta.url), 'utf8');
    const catalogPicker = screen.slice(
      screen.indexOf('<Card variant="creative" style={{ gap: 10 }}>'),
      screen.indexOf('{props.busy ? <ParentAiLoadingState'),
    );
    expect(catalogPicker).toContain('props.catalogGuides.length === 0');
    expect(catalogPicker).toContain('props.catalogGuidesError');
    expect(catalogPicker).toContain('props.canCreateGuide ? <SecondaryButton');
    expect(catalogPicker).toContain('disabled={props.busy}');
    expect(catalogPicker).toContain('label="Tạo hướng dẫn bằng AI"');
    expect(catalogPicker).toContain('Bản nháp AI chỉ được tạo khi người lớn yêu cầu.');

    const app = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    expect(app).toContain('canCreateGuide={parent.guideEnabled}');
    expect(app).toContain('catalogGuidePickerOpen={parent.catalogGuidePickerOpen}');

    const controller = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const openDrawingGuide = controller.slice(
      controller.indexOf('function openDrawingGuide(): void {'),
      controller.indexOf('function continueAfterSketchGuide(): void {'),
    );
    expect(openDrawingGuide).toContain("setStep(lesson ? 'drawing-guide' : 'capture')");
    expect(openDrawingGuide).not.toContain('createGuide(');
  });

  it('exposes catalog listing through the learning use case', async () => {
    const list = vi.fn(async () => ({ contract: 'SvgGuideCatalogPageV1' as const, items: [] }));
    const useCases = new ParentLearningUseCases({ listSvgCatalogGuides: list } as unknown as ParentApiPort);
    await useCases.listSvgCatalogGuides('sea-creatures', 9);
    expect(list).toHaveBeenCalledWith('sea-creatures', 9);
  });
});
