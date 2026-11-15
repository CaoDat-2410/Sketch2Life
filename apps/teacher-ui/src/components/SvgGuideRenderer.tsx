import { useState } from 'react'
import type { ProgressiveStrokeGuideV1, SvgDocumentV1 } from '../domain/svgGuide'
import { orderedVisiblePathIds } from '../domain/svgGuide'

type Props = Readonly<{
  document: SvgDocumentV1
  guide: ProgressiveStrokeGuideV1
  stageIndex?: number
  onStageIndexChange?: (next: number) => void
  compact?: boolean
}>

export function SvgGuideRenderer({ document, guide, stageIndex, onStageIndexChange, compact = false }: Props) {
  const [localStage, setLocalStage] = useState(0)
  const activeIndex = stageIndex ?? localStage
  const safeIndex = Math.min(guide.stages.length - 1, Math.max(0, activeIndex))
  const stage = guide.stages[safeIndex]
  const pathById = new Map(document.paths.map((path) => [path.path_id, path] as const))
  const visiblePaths = orderedVisiblePathIds(guide, safeIndex).flatMap((pathId) => {
    const path = pathById.get(pathId)
    return path ? [path] : []
  })
  const dashed = new Set(stage?.new_path_ids ?? [])

  function move(next: number) {
    const value = Math.min(guide.stages.length - 1, Math.max(0, next))
    if (stageIndex === undefined) setLocalStage(value)
    onStageIndexChange?.(value)
  }

  return (
    <section className={`flex min-h-0 flex-col ${compact ? 'gap-2' : 'gap-3'}`} aria-label={`Hướng dẫn vẽ: ${guide.title_vi}`}>
      {!compact && <div className="text-center">
        <p className="text-sm font-semibold text-slate-500">Bước {safeIndex + 1} / {guide.stages.length}</p>
        <p className="mt-1 font-semibold text-slate-900">{stage?.instruction_vi}</p>
      </div>}
      <div className="min-h-0 aspect-square w-full overflow-hidden rounded-xl border border-slate-200 bg-white p-3 transition-opacity duration-150" aria-live="polite">
        <svg viewBox={document.view_box} role="img" aria-label={`${guide.title_vi}, bước ${safeIndex + 1}`} className="h-full w-full">
          {visiblePaths.map((path) => (
            <path
              key={path.path_id}
              d={path.d}
              fill="none"
              stroke={path.stroke}
              strokeWidth={path.stroke_width}
              strokeDasharray={dashed.has(path.path_id) ? '8 6' : undefined}
              strokeLinecap="round"
              strokeLinejoin="round"
              data-path-id={path.path_id}
            />
          ))}
        </svg>
      </div>
      <div className="flex items-center justify-between gap-2">
        <button type="button" onClick={() => move(safeIndex - 1)} disabled={safeIndex === 0} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-40">Bước trước</button>
        <div className="flex items-center gap-1.5" aria-label="Chọn bước">
          {guide.stages.map((item, index) => <button
            key={item.step_index}
            type="button"
            aria-label={`Mở bước ${item.step_index}`}
            aria-current={index === safeIndex ? 'step' : undefined}
            onClick={() => move(index)}
            className={`h-2.5 w-6 rounded-full ${index === safeIndex ? 'bg-blue-700' : 'bg-slate-300 hover:bg-slate-400'}`}
          />)}
        </div>
        <button type="button" onClick={() => move(safeIndex + 1)} disabled={safeIndex >= guide.stages.length - 1} className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40">Bước tiếp</button>
      </div>
    </section>
  )
}
