import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const evidenceDir = path.dirname(fileURLToPath(import.meta.url));
const candidateDir = path.join(evidenceDir, 'candidates');
const runtimeDir = path.resolve(evidenceDir, '../../../../deployment/modal/srs_v23/data/openclipart');
fs.mkdirSync(runtimeDir, { recursive: true });

const numberToken = /[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?/;
const tokenPattern = new RegExp(`[AaCcHhLlMmQqSsTtVvZz]|${numberToken.source}`, 'g');
const commandArity = { a: 7, c: 6, h: 1, l: 2, m: 2, q: 4, s: 4, t: 2, v: 1 };
const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const round = (number) => Number(number.toFixed(6)).toString();

function tokensFor(d) {
  return [...d.matchAll(tokenPattern)].map((match) => ({
    value: match[0],
    index: match.index,
    end: match.index + match[0].length,
  }));
}

function splitSubpaths(d) {
  const tokens = tokensFor(d);
  const starts = tokens
    .map((token, tokenIndex) => ({ ...token, tokenIndex }))
    .filter(({ value }) => value === 'M' || value === 'm');
  if (!starts.length) throw new Error('SOURCE_PATH_HAS_NO_MOVETO');
  let current = { x: 0, y: 0 };
  const result = [];

  for (let partIndex = 0; partIndex < starts.length; partIndex += 1) {
    const start = starts[partIndex];
    const next = starts[partIndex + 1];
    const endIndex = next?.tokenIndex ?? tokens.length;
    const rawX = Number(tokens[start.tokenIndex + 1]?.value);
    const rawY = Number(tokens[start.tokenIndex + 2]?.value);
    if (!Number.isFinite(rawX) || !Number.isFinite(rawY)) throw new Error('SOURCE_MOVETO_INVALID');
    const point = start.value === 'M' ? { x: rawX, y: rawY } : { x: current.x + rawX, y: current.y + rawY };
    const initial = point;
    let cursor = start.tokenIndex + 3;
    while (cursor < endIndex && !/^[A-Za-z]$/.test(tokens[cursor].value)) cursor += 1;
    const extra = tokens.slice(start.tokenIndex + 3, cursor).map(({ value }) => Number(value));
    if (extra.length % 2) throw new Error('SOURCE_MOVETO_PAIR_INVALID');
    let moved = point;
    let extraLines = '';
    for (let offset = 0; offset < extra.length; offset += 2) {
      moved = start.value === 'M'
        ? { x: extra[offset], y: extra[offset + 1] }
        : { x: moved.x + extra[offset], y: moved.y + extra[offset + 1] };
      extraLines += `L${round(moved.x)} ${round(moved.y)}`;
    }
    const tailStart = tokens[cursor]?.index ?? next?.index ?? d.length;
    current = moved;
    let command = null;
    while (cursor < endIndex) {
      if (/^[A-Za-z]$/.test(tokens[cursor].value)) {
        command = tokens[cursor].value;
        cursor += 1;
        if (command.toLowerCase() === 'z') {
          current = initial;
          command = null;
          continue;
        }
      }
      if (!command) throw new Error('SOURCE_COMMAND_MISSING');
      const arity = commandArity[command.toLowerCase()];
      const values = [];
      while (cursor < endIndex && !/^[A-Za-z]$/.test(tokens[cursor].value)) {
        values.push(Number(tokens[cursor].value));
        cursor += 1;
      }
      if (!values.length || values.length % arity) throw new Error(`SOURCE_COMMAND_ARITY:${command}`);
      for (let offset = 0; offset < values.length; offset += arity) {
        const tuple = values.slice(offset, offset + arity);
        const relative = command === command.toLowerCase();
        const lower = command.toLowerCase();
        if (lower === 'h') current.x = relative ? current.x + tuple[0] : tuple[0];
        else if (lower === 'v') current.y = relative ? current.y + tuple[0] : tuple[0];
        else {
          const endpointX = lower === 'a' ? tuple[5] : tuple[arity - 2];
          const endpointY = lower === 'a' ? tuple[6] : tuple[arity - 1];
          current = relative
            ? { x: current.x + endpointX, y: current.y + endpointY }
            : { x: endpointX, y: endpointY };
        }
      }
    }
    const tailEnd = next?.index ?? d.length;
    result.push({ d: `M${round(point.x)} ${round(point.y)}${extraLines}${d.slice(tailStart, tailEnd)}`.trim() });
  }
  return result;
}

function transformPathData(d, matrix) {
  if (!matrix) return d.trim();
  const [a, b, c, scaleY, e, f] = matrix;
  if (Math.abs(a * c + b * scaleY) > 1e-8 || Math.abs(a * a + b * b - scaleY * scaleY - c * c) > 1e-6) {
    throw new Error('SOURCE_AFFINE_MATRIX_NOT_SUPPORTED');
  }
  const tokens = tokensFor(d);
  const arity = { a: 7, c: 6, h: 1, l: 2, m: 2, q: 4, s: 4, t: 2, v: 1 };
  let cursor = 0;
  let command = null;
  let current = { x: 0, y: 0 };
  let subpathStart = current;
  const output = [];
  const mapPoint = ({ x, y }) => ({ x: a * x + c * y + e, y: b * x + scaleY * y + f });

  while (cursor < tokens.length) {
    if (/^[A-Za-z]$/.test(tokens[cursor].value)) {
      command = tokens[cursor].value;
      cursor += 1;
      const lower = command.toLowerCase();
      if (lower === 'z') {
        output.push('Z');
        current = subpathStart;
        continue;
      }
    }
    if (!command) throw new Error('SOURCE_PATH_COMMAND_MISSING');
    const lower = command.toLowerCase();
    const count = arity[lower];
    if (!count) throw new Error(`SOURCE_PATH_COMMAND_UNSUPPORTED:${command}`);
    const values = [];
    while (cursor < tokens.length && !/^[A-Za-z]$/.test(tokens[cursor].value)) {
      values.push(Number(tokens[cursor].value));
      cursor += 1;
    }
    if (!values.length || values.length % count) throw new Error(`SOURCE_PATH_ARITY:${command}`);
    const relative = command === command.toLowerCase();
    for (let offset = 0; offset < values.length; offset += count) {
      const tuple = values.slice(offset, offset + count);
      if (lower === 'h' || lower === 'v') {
        const endpoint = lower === 'h'
          ? { x: relative ? current.x + tuple[0] : tuple[0], y: current.y }
          : { x: current.x, y: relative ? current.y + tuple[0] : tuple[0] };
        const mapped = mapPoint(endpoint);
        output.push(`L${round(mapped.x)} ${round(mapped.y)}`);
        current = endpoint;
        continue;
      }
      const pointPairs = lower === 'c' ? [0, 2, 4]
        : lower === 's' || lower === 'q' ? [0, 2]
          : lower === 'a' ? [5]
            : lower === 'm' || lower === 'l' || lower === 't' ? [0]
              : [];
      if (lower === 'a' && Math.abs(a - scaleY) > 1e-8) throw new Error('SOURCE_ARC_NONUNIFORM_TRANSFORM');
      const mappedTuple = [...tuple];
      for (const pair of pointPairs) {
        const point = relative
          ? { x: current.x + tuple[pair], y: current.y + tuple[pair + 1] }
          : { x: tuple[pair], y: tuple[pair + 1] };
        const mapped = mapPoint(point);
        mappedTuple[pair] = mapped.x;
        mappedTuple[pair + 1] = mapped.y;
        if (pair === pointPairs.at(-1)) current = point;
      }
      if (lower === 'a') {
        mappedTuple[0] *= Math.abs(a);
        mappedTuple[1] *= Math.abs(a);
        mappedTuple[2] += Math.atan2(b, a) * 180 / Math.PI;
      }
      const outputCommand = lower === 'm'
        ? (offset === 0 ? 'M' : 'L')
        : lower === 'l' ? 'L'
        : lower.toUpperCase();
      const mappedText = mappedTuple.map(round).join(' ');
      output.push(`${outputCommand}${mappedText}`);
      if (lower === 'm') {
        subpathStart = current;
      }
    }
  }
  return output.join(' ');
}

function parseMatrix(transform) {
  if (!transform) return null;
  const matrix = transform.match(/matrix\(([^)]+)\)/);
  if (matrix) return matrix[1].split(/[ ,]+/).map(Number);
  const translation = transform.match(/translate\(([^)]+)\)/);
  if (translation) {
    const [x = 0, y = 0] = translation[1].split(/[ ,]+/).map(Number);
    return [1, 0, 0, 1, x, y];
  }
  throw new Error(`SOURCE_TRANSFORM_UNSUPPORTED:${transform}`);
}

function parseAttributes(tag) {
  const attributes = {};
  for (const match of tag.matchAll(/([A-Za-z_:][\w:.-]*)="([^"]*)"/g)) attributes[match[1]] = match[2];
  return attributes;
}

function pathElements(fragment) {
  return [...fragment.matchAll(/<path\b[^>]*\/?\s*>/g)].map((match) => parseAttributes(match[0]));
}

function groupById(svg, id) {
  const match = [...svg.matchAll(/<g\b[^>]*>/g)].find((item) => parseAttributes(item[0]).id === id);
  if (!match) return null;
  const close = svg.indexOf('</g>', match.index + match[0].length);
  if (close < 0) throw new Error(`SOURCE_GROUP_UNCLOSED:${id}`);
  return { attributes: parseAttributes(match[0]), body: svg.slice(match.index + match[0].length, close) };
}

function colorValue(pathAttributes) {
  let fill = pathAttributes.fill;
  if (!fill && pathAttributes.style) fill = pathAttributes.style.match(/(?:^|;)\s*fill\s*:\s*([^;]+)/)?.[1]?.trim();
  fill ??= '#000000';
  const rgb = fill.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
  if (rgb) fill = `#${rgb.slice(1).map((channel) => Number(channel).toString(16).padStart(2, '0')).join('')}`;
  if (!/^#[0-9a-fA-F]{6}$/.test(fill)) throw new Error(`SOURCE_COLOR_UNSUPPORTED:${fill}`);
  return fill.toLowerCase();
}

function makeReferencePath(id, d, fill, stroke = fill, strokeWidth = 0.1) {
  return {
    path_id: id,
    d,
    fill,
    stroke,
    stroke_width: strokeWidth,
    stroke_linecap: 'round',
    stroke_linejoin: 'round',
  };
}

function loadPair(animal) {
  const colorName = `${animal}-color.svg`;
  const lineName = `${animal}-line.svg`;
  const colorBytes = fs.readFileSync(path.join(candidateDir, colorName));
  const lineBytes = fs.readFileSync(path.join(candidateDir, lineName));
  const colorSource = colorBytes.toString('utf8');
  const lineSource = lineBytes.toString('utf8');
  const colorViewBox = colorSource.match(/\bviewBox="([^"]+)"/)?.[1];
  const lineViewBox = lineSource.match(/\bviewBox="([^"]+)"/)?.[1];
  if (!colorViewBox || !lineViewBox) throw new Error(`${animal}: VIEWBOX_MISSING`);

  let guideSubpaths;
  let guideViewBox;
  let referencePaths = [];
  let referenceViewBox = colorViewBox;
  let lineTransform = null;
  if (animal === 'butterfly') {
    const lineGroup = groupById(lineSource, 'Simple-Detailed-Butterfly-Outline');
    const colorGroup = groupById(colorSource, 'Fill-Color');
    if (!lineGroup || !colorGroup) throw new Error('BUTTERFLY_SOURCE_GROUP_MISSING');
    const rawLine = pathElements(lineGroup.body)[0]?.d;
    if (!rawLine) throw new Error('BUTTERFLY_LINE_PATH_MISSING');
    lineTransform = parseMatrix(lineGroup.attributes.transform);
    guideSubpaths = splitSubpaths(rawLine).map(({ d }) => transformPathData(d, lineTransform));
    guideViewBox = '0 0 500 500';
    referencePaths = pathElements(colorGroup.body).map((item, index) => ({
      ...makeReferencePath(`reference-color-${String(index + 1).padStart(3, '0')}`, item.d, colorValue(item)),
    }));
    referencePaths.push(...guideSubpaths.map((d, index) => makeReferencePath(
      `reference-outline-${String(index + 1).padStart(3, '0')}`,
      d,
      'none',
      '#000000',
      1.2,
    )));
    referenceViewBox = '0 0 500 500';
  } else {
    const linePath = lineSource.match(/<path\b[^>]*>/)?.[0];
    const lineD = linePath ? parseAttributes(linePath).d : null;
    const colorGroup = [...colorSource.matchAll(/<g\b[^>]*>/g)][0];
    if (!lineD || !colorGroup) throw new Error('TURTLE_SOURCE_PATH_MISSING');
    const colorGroupStart = colorGroup.index + colorGroup[0].length;
    const colorGroupEnd = colorSource.indexOf('</g>', colorGroupStart);
    const groupAttributes = parseAttributes(colorGroup[0]);
    guideSubpaths = splitSubpaths(lineD).map(({ d }) => d);
    guideViewBox = lineViewBox;
    referencePaths = pathElements(colorSource.slice(colorGroupStart, colorGroupEnd)).map((item, index) => {
      const fill = colorValue(item);
      return makeReferencePath(`reference-color-${String(index + 1).padStart(3, '0')}`, item.d, fill);
    });
    referenceViewBox = groupAttributes.transform === 'translate(4,4)'
      ? '-4 -4 256 200'
      : colorViewBox;
  }

  const guidePaths = guideSubpaths.map((d, index) => ({
    path_id: `source-contour-${String(index + 1).padStart(3, '0')}`,
    source_path_id: `openclipart-source-${animal === 'butterfly' ? '352671' : '325116'}-path-001-subpath-${String(index + 1).padStart(3, '0')}`,
    d,
    fill: 'none',
    stroke: '#20293b',
    stroke_width: animal === 'butterfly' ? 1.2 : 0.65,
  }));
  const stageGroups = animal === 'butterfly'
    ? [7, 6, 7, 6, 7, 6]
    : [6, 6, 6, 6, 6, 5];
  if (stageGroups.reduce((sum, count) => sum + count, 0) !== guidePaths.length) {
    throw new Error(`${animal}: STAGE_PATH_COVERAGE_INVALID`);
  }
  const stageLabels = animal === 'butterfly'
    ? [
        ['Đường bao đôi cánh', 'Vẽ nét bao lớn để tạo dáng hai cánh bướm.'],
        ['Thân và râu bướm', 'Thêm phần thân nhỏ và hai chiếc râu cong.'],
        ['Nét cong trên cánh', 'Bổ sung các đường cong lớn trên cánh.'],
        ['Họa tiết cánh phải', 'Vẽ thêm các mảng cong ở cánh bên phải.'],
        ['Họa tiết cánh trái', 'Thêm các mảng cong ở cánh bên trái.'],
        ['Hoàn thiện cánh', 'Bổ sung các nét nhỏ để hoàn thành hình bướm.'],
      ]
    : [
        ['Dáng mai và thân', 'Vẽ đường bao cong lớn của mai và thân rùa.'],
        ['Đầu và cổ', 'Thêm đầu, mắt và phần cổ nhô ra phía trước.'],
        ['Nét lớn trên mai', 'Chia mai thành vài mảng lớn dễ nhận biết.'],
        ['Chân rùa', 'Thêm các nét chân ở dưới mai.'],
        ['Các ô trên mai', 'Bổ sung thêm những ô lớn trên mai rùa.'],
        ['Hoàn thiện mai', 'Thêm các nét còn lại để hoàn thành mai rùa.'],
      ];
  let offset = 0;
  const stages = stageGroups.map((count, index) => {
    const pathIds = guidePaths.slice(offset, offset + count).map(({ path_id }) => path_id);
    offset += count;
    const [label_vi, instruction_vi] = stageLabels[index];
    return {
      step_index: index + 1,
      part_id: `${animal}-step-${index + 1}`,
      label_vi,
      instruction_vi,
      path_ids: pathIds,
    };
  });
  const guideData = {
    schema_version: 'OpenclipartParentGuideDataV1',
    asset_id: `openclipart-${animal}-illustration-v1`,
    title_vi: animal === 'butterfly' ? 'Vẽ con bướm' : 'Vẽ con rùa',
    guide_view_box: guideViewBox,
    guide_paths: guidePaths,
    stages,
    reference_view_box: referenceViewBox,
    reference_paths: referencePaths,
    topic_aliases: animal === 'butterfly'
      ? ['bướm', 'con bướm', 'butterfly']
      : ['rùa', 'con rùa', 'turtle', 'tortoise'],
    source: {
      dataset_name: 'Openclipart',
      dataset_revision: '2026-11-14-curated',
      license_id: 'CC0-1.0',
      license_uri: 'https://creativecommons.org/publicdomain/zero/1.0/',
      attribution: animal === 'butterfly' ? 'teck5' : 'hund',
      color_asset_id: animal === 'butterfly' ? '352665' : '325115',
      line_asset_id: animal === 'butterfly' ? '352671' : '325116',
      color_source_file: colorName,
      line_source_file: lineName,
      color_sha256: sha256(colorBytes),
      line_sha256: sha256(lineBytes),
      color_source_uri: animal === 'butterfly'
        ? 'https://openclipart.org/detail/352665/simple-detailed-butterfly-clipart'
        : 'https://openclipart.org/detail/325115/turtle-crawling-color',
      line_source_uri: animal === 'butterfly'
        ? 'https://openclipart.org/detail/352671/simple-detailed-butterfly-lineart'
        : 'https://openclipart.org/detail/325116/turtle-crawling-line-art',
      line_derivation: 'SPLIT_SOURCE_CONTOURS_AND_TRANSFORM_TO_GUIDE_VIEWBOX_V1',
    },
  };
  const filename = `${animal}-guide.json`;
  const data = Buffer.from(`${JSON.stringify(guideData, null, 2)}\n`);
  fs.writeFileSync(path.join(runtimeDir, filename), data);
  fs.copyFileSync(path.join(candidateDir, colorName), path.join(runtimeDir, colorName));
  fs.copyFileSync(path.join(candidateDir, lineName), path.join(runtimeDir, lineName));
  return {
    asset_id: guideData.asset_id,
    title_vi: guideData.title_vi,
    topic_aliases: guideData.topic_aliases,
    guide_data_file: filename,
    guide_data_sha256: sha256(data),
    color_source_file: colorName,
    color_sha256: guideData.source.color_sha256,
    color_source_uri: guideData.source.color_source_uri,
    line_source_file: lineName,
    line_sha256: guideData.source.line_sha256,
    line_source_uri: guideData.source.line_source_uri,
    attribution: guideData.source.attribution,
    license_id: guideData.source.license_id,
    license_uri: guideData.source.license_uri,
    stage_count: stages.length,
    guide_path_count: guidePaths.length,
    reference_path_count: referencePaths.length,
  };
}

const assets = ['butterfly', 'turtle'].map(loadPair);
const manifest = {
  schema_version: 'OpenclipartParentGuideManifestV1',
  dataset_name: 'Openclipart',
  dataset_revision: '2026-11-14-curated',
  license_id: 'CC0-1.0',
  license_uri: 'https://creativecommons.org/publicdomain/zero/1.0/',
  license_notice_file: 'NOTICE.md',
  assets,
};
const manifestBytes = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`);
fs.writeFileSync(path.join(runtimeDir, 'parent-guide-manifest.json'), manifestBytes);
fs.writeFileSync(
  path.join(runtimeDir, 'NOTICE.md'),
  [
    '# Openclipart source pack',
    '',
    'Individually curated SVG source files from Openclipart. Openclipart states uploaded artwork is dedicated to the public domain under CC0 1.0.',
    'License: https://creativecommons.org/publicdomain/zero/1.0/',
    '',
    ...assets.flatMap((asset) => [
      `## ${asset.title_vi} — ${asset.attribution}`,
      `- Color source: ${asset.color_source_uri} (asset ${asset.color_source_file === 'butterfly-color.svg' ? '352665' : '325115'}), SHA-256 ${asset.color_sha256}.`,
      `- Line source: ${asset.line_source_uri} (asset ${asset.line_source_file === 'butterfly-line.svg' ? '352671' : '325116'}), SHA-256 ${asset.line_sha256}.`,
      `- Curated guide: ${asset.guide_data_file}, SHA-256 ${asset.guide_data_sha256}.`,
      `- Adaptation: split source path contours into progressive 6-step guide paths; color reference retains the source's matching view and palette.`,
      '',
    ]),
    'The dog candidate was inspected but not packaged because its fur contour is too dense for the intended age range.',
    '',
  ].join('\n'),
);
process.stdout.write(`manifest_sha256=${sha256(manifestBytes)}\n`);
for (const asset of assets) process.stdout.write(`${JSON.stringify(asset)}\n`);
