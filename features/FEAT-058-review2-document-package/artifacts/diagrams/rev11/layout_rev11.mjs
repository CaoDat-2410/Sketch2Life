import fs from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ELK = require(process.env.ELK_MODULE_PATH);

const inputPath = process.argv[2];
const outputPath = process.argv[3];
if (!inputPath || !outputPath) throw new Error('usage: layout_rev11.mjs input.json output.json');

const elk = new ELK();
const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const outputs = [];

for (const diagram of input) {
  const isActivity = diagram.kind === 'activity';
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'DOWN',
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.aspectRatio': '1.35',
      'elk.spacing.nodeNode': isActivity ? '30' : '28',
      'elk.spacing.edgeNode': '18',
      // Reserve visible white space around label plaques, not only their
      // mathematical bounds. The preview and Draw.io cells add a small border.
      'elk.spacing.edgeEdge': '32',
      'elk.layered.spacing.nodeNodeBetweenLayers': isActivity ? '48' : '48',
      'elk.layered.spacing.edgeNodeBetweenLayers': '18',
      'elk.layered.spacing.edgeEdgeBetweenLayers': '32',
      'elk.layered.edgeLabels.placement': 'CENTER',
      'elk.layered.edgeLabels.sideSelection': 'SMART_DOWN',
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
      'elk.padding': '[top=16,left=24,bottom=18,right=24]',
    },
    children: diagram.nodes.map((node) => ({
      id: node.id,
      width: node.width,
      height: node.height,
      labels: [{ text: node.label, width: Math.max(40, node.width - 28), height: Math.max(24, node.height - 12) }],
      layoutOptions: node.kind === 'note'
        ? { 'elk.layered.layerConstraint': 'LAST' }
        : node.kind === 'start'
          ? { 'elk.layered.layerConstraint': 'FIRST' }
          : undefined,
    })),
    edges: diagram.edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
      labels: edge.label ? [{ text: edge.label, width: edge.labelWidth, height: edge.labelHeight }] : undefined,
      layoutOptions: edge.relation ? { 'elk.edgeRouting': 'ORTHOGONAL' } : undefined,
    })),
  };
  const result = await elk.layout(graph);
  outputs.push({ ...diagram, layout: result });
}

fs.writeFileSync(outputPath, JSON.stringify(outputs));
