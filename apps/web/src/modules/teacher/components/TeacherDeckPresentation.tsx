import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { TeacherProgressiveDrawing, hasTeacherDrawing } from "./TeacherProgressiveDrawing";

type SlideKind = 'orientation' | 'drawing_guide' | 'subject_exploration' | 'approved_activity'

type DrawingStep = Readonly<{
  stepIndex: number
  instruction: string
  placement: string
  drawing?: ProgressiveDrawing
}>

type DrawingBase = Readonly<{ stroke: string; stroke_width: number }>
type DrawingStroke =
  | (DrawingBase & Readonly<{ kind: 'circle'; cx: number; cy: number; r: number }>)
  | (DrawingBase & Readonly<{ kind: 'ellipse'; cx: number; cy: number; rx: number; ry: number }>)
  | (DrawingBase & Readonly<{ kind: 'rect'; x: number; y: number; w: number; h: number }>)
  | (DrawingBase & Readonly<{ kind: 'line'; x1: number; y1: number; x2: number; y2: number }>)
  | (DrawingBase & Readonly<{ kind: 'polyline'; points: readonly (readonly [number, number])[] }>)

export type ProgressiveDrawing = Readonly<{
  viewbox: readonly [number, number, number, number]
  strokes: readonly DrawingStroke[]
  source: 'catalog' | 'recipe' | 'ai_draft'
  sha256: string
  caption?: string
}>

type DeckSlide = Readonly<{
  slideIndex: number
  kind: SlideKind
  title: string
  activityRef: string | null
  bullets: string[]
  steps: DrawingStep[]
  goal: string[]
  materials: string[]
  preparation: string[]
  instructions: string[]
  safetyNotes: string[]
}>

export type TeacherSketchDeck = Readonly<{
  topic: string
  ageMonths: number
  slides: DeckSlide[]
}>

type Props = Readonly<{
  deck: TeacherSketchDeck
  onClose: () => void
}>

const ALLOWED_KINDS = new Set<SlideKind>([
  'orientation',
  'drawing_guide',
  'subject_exploration',
  'approved_activity',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function finiteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= 10_000
}

function parseDrawingStroke(value: unknown): DrawingStroke | null {
  if (!isRecord(value)
    || typeof value.kind !== 'string'
    || typeof value.stroke !== 'string'
    || !/^#[0-9a-f]{6}$/i.test(value.stroke)
    || !finiteNumber(value.stroke_width)
    || value.stroke_width < 0.25
    || value.stroke_width > 64) return null
  const numbers = (keys: string[]) => {
    const result: number[] = []
    for (const key of keys) {
      if (!finiteNumber(value[key])) return null
      result.push(value[key])
    }
    return result
  }
  const fieldsAre = (keys: string[]) => Object.keys(value).sort().join(',')
    === [...keys, 'kind', 'stroke', 'stroke_width'].sort().join(',')
  switch (value.kind) {
    case 'circle': {
      const geometry = numbers(['cx', 'cy', 'r'])
      if (!fieldsAre(['cx', 'cy', 'r']) || !geometry || geometry[2] <= 0) return null
      const [cx, cy, r] = geometry
      return { kind: 'circle', cx, cy, r, stroke: value.stroke, stroke_width: value.stroke_width }
    }
    case 'ellipse': {
      const geometry = numbers(['cx', 'cy', 'rx', 'ry'])
      if (!fieldsAre(['cx', 'cy', 'rx', 'ry']) || !geometry || geometry[2] <= 0 || geometry[3] <= 0) return null
      const [cx, cy, rx, ry] = geometry
      return { kind: 'ellipse', cx, cy, rx, ry, stroke: value.stroke, stroke_width: value.stroke_width }
    }
    case 'rect': {
      const geometry = numbers(['x', 'y', 'w', 'h'])
      if (!fieldsAre(['x', 'y', 'w', 'h']) || !geometry || geometry[2] <= 0 || geometry[3] <= 0) return null
      const [x, y, w, h] = geometry
      return { kind: 'rect', x, y, w, h, stroke: value.stroke, stroke_width: value.stroke_width }
    }
    case 'line': {
      const geometry = numbers(['x1', 'y1', 'x2', 'y2'])
      if (!fieldsAre(['x1', 'y1', 'x2', 'y2']) || !geometry) return null
      const [x1, y1, x2, y2] = geometry
      return { kind: 'line', x1, y1, x2, y2, stroke: value.stroke, stroke_width: value.stroke_width }
    }
    case 'polyline': {
      if (!fieldsAre(['points']) || !Array.isArray(value.points) || value.points.length < 2 || value.points.length > 256) return null
      const points: [number, number][] = []
      for (const point of value.points) {
        if (!Array.isArray(point) || point.length !== 2 || !finiteNumber(point[0]) || !finiteNumber(point[1])) return null
        points.push([point[0], point[1]])
      }
      return { kind: 'polyline', points, stroke: value.stroke, stroke_width: value.stroke_width }
    }
    default:
      return null
  }
}

export function parseProgressiveDrawing(value: unknown): ProgressiveDrawing | null {
  if (!isRecord(value)
    || !Array.isArray(value.viewbox)
    || value.viewbox.length !== 4
    || !value.viewbox.every(finiteNumber)
    || value.viewbox[2] <= 0
    || value.viewbox[3] <= 0
    || !Array.isArray(value.strokes)
    || value.strokes.length > 256
    || (value.source !== 'catalog' && value.source !== 'recipe' && value.source !== 'ai_draft')
    || typeof value.sha256 !== 'string'
    || !/^[0-9a-f]{64}$/.test(value.sha256)) return null
  const strokes: DrawingStroke[] = []
  for (const item of value.strokes) {
    const stroke = parseDrawingStroke(item)
    if (!stroke) return null
    strokes.push(stroke)
  }
  return {
    viewbox: [value.viewbox[0], value.viewbox[1], value.viewbox[2], value.viewbox[3]],
    strokes,
    source: value.source,
    sha256: value.sha256,
    ...(typeof value.caption === 'string' && value.caption.trim() && value.caption.length <= 600 ? { caption: value.caption.trim() } : {}),
  }
}

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function textList(value: unknown): string[] {
  const splitLines = (item: unknown): string[] => {
    if (typeof item !== 'string') return []
    const lines = item.replace(/\\n/g, '\n').split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
    return lines.reduce<string[]>((items, line) => {
      if (!items.length || /^(?:\d+[.)]|[-•])\s/.test(line)) items.push(line)
      else items[items.length - 1] = `${items[items.length - 1]} ${line}`
      return items
    }, [])
  }
  const lines = typeof value === 'string'
    ? splitLines(value)
    : Array.isArray(value)
      ? value.flatMap(splitLines)
      : []
  return lines.reduce<string[]>((items, line) => {
    const previous = items[items.length - 1]
    if (previous && /^\d+[.)]\s/.test(previous) && !/^\d+[.)]\s/.test(line)) {
      items[items.length - 1] = `${previous} ${line}`
    } else {
      items.push(line)
    }
    return items
  }, [])
}

export function parseTeacherSketchDeck(value: unknown): TeacherSketchDeck | null {
  if (!isRecord(value)
    || value.schema_version !== 'sketch2life.teacher-sketch-deck.v1'
    || value.status !== 'DRAFT'
    || value.aspect_ratio !== '16:9'
    || value.review_required !== true
    || typeof value.topic !== 'string'
    || !value.topic.trim()
    || typeof value.target_age_months !== 'number'
    || !Number.isInteger(value.target_age_months)
    || !Array.isArray(value.slides)
    || value.slides.length < 1) return null

  const slides: DeckSlide[] = []
  for (const [index, item] of value.slides.entries()) {
    if (!isRecord(item)
      || item.slide_index !== index + 1
      || typeof item.kind !== 'string'
      || !ALLOWED_KINDS.has(item.kind as SlideKind)
      || typeof item.title !== 'string'
      || !item.title.trim()) return null

    const kind = item.kind as SlideKind
    const steps: DrawingStep[] = []
    if (kind === 'drawing_guide') {
      if (!Array.isArray(item.steps) || item.steps.length < 3 || item.steps.length > 8) return null
      for (const [stepIndex, rawStep] of item.steps.entries()) {
        if (!isRecord(rawStep)
          || rawStep.step_index !== stepIndex + 1
          || typeof rawStep.instruction !== 'string'
          || !rawStep.instruction.trim()
          || typeof rawStep.placement !== 'string'
          || !rawStep.placement.trim()) return null
        steps.push({
          stepIndex: stepIndex + 1,
          instruction: rawStep.instruction.trim(),
          placement: rawStep.placement.trim(),
        })
      }
    }

    if (kind === 'approved_activity' && !text(item.activity_ref)) return null
    slides.push({
      slideIndex: index + 1,
      kind,
      title: item.title.trim(),
      activityRef: text(item.activity_ref) || null,
      bullets: textList(item.bullets),
      steps,
      goal: textList(item.goal),
      materials: textList(item.materials),
      preparation: textList(item.preparation),
      instructions: textList(item.instructions),
      safetyNotes: textList(item.safety_notes),
    })
  }

  return {
    topic: value.topic.trim(),
    ageMonths: value.target_age_months,
    slides,
  }
}

function kindLabel(kind: SlideKind): string {
  switch (kind) {
    case 'orientation': return 'Mở đầu'
    case 'drawing_guide': return 'Quan sát và vẽ'
    case 'subject_exploration': return 'Tìm hiểu chủ đề'
    case 'approved_activity': return 'Hoạt động đã duyệt'
  }
}

function TextList({ items, emptyLabel }: { items: string[]; emptyLabel?: string }) {
  if (!items.length) return emptyLabel ? <p className="text-slate-500">{emptyLabel}</p> : null
  return <ul className="space-y-2">{items.map((item, index) => <li key={`${index}-${item}`} className="flex gap-3 text-slate-800"><span aria-hidden="true" className="mt-[0.55rem] h-2 w-2 shrink-0 rounded-full bg-blue-600" /><span>{item}</span></li>)}</ul>
}

export function TeacherDeckPresentation({
  deck,
  onClose,
}: Props) {
  const [slideIndex, setSlideIndex] = useState(0)
  const [stepIndex, setStepIndex] = useState(0)
  const slide = deck.slides[slideIndex]
  const currentStep = slide.kind === 'drawing_guide' ? slide.steps[stepIndex] : null
  const showsDrawing = slide.kind === 'drawing_guide' && hasTeacherDrawing(slide.steps)
  const nextStepLabel = slide.kind !== 'drawing_guide' || stepIndex + 1 < slide.steps.length
    ? 'Bước tiếp theo'
    : slideIndex + 1 < deck.slides.length
      ? 'Slide tiếp theo'
      : 'Bắt đầu lại'

  function selectSlide(index: number) {
    setSlideIndex(index)
    setStepIndex(0)
  }

  function moveSlide(direction: -1 | 1) {
    selectSlide(Math.min(deck.slides.length - 1, Math.max(0, slideIndex + direction)))
  }

  function moveStep(direction: -1 | 1) {
    if (slide.kind !== 'drawing_guide') return
    setStepIndex((current) => Math.min(slide.steps.length - 1, Math.max(0, current + direction)))
  }

  function skipStep() {
    if (slide.kind !== 'drawing_guide') return
    if (stepIndex + 1 < slide.steps.length) setStepIndex((current) => current + 1)
    else moveSlide(1)
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault()
        moveSlide(-1)
      } else if (event.key === 'ArrowRight') {
        event.preventDefault()
        moveSlide(1)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [slideIndex, onClose])

  return createPortal(
    <div className="teacher-deck-presentation fixed inset-0 z-[100] flex flex-col bg-slate-950 p-3 text-white sm:p-5" role="dialog" aria-modal="true" aria-label="Trình chiếu Sketch Deck">
      <header className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-4 pb-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold uppercase tracking-[0.16em] text-slate-300">Sketch Deck · {deck.topic}</p>
          <p className="mt-1 text-xs text-amber-200">Bản nháp · cần giáo viên rà soát trước khi sử dụng</p>
        </div>
        <button type="button" onClick={onClose} className="shrink-0 rounded-lg border border-slate-500 px-4 py-2 text-sm font-semibold hover:bg-slate-800" aria-label="Đóng trình chiếu">Đóng <span aria-hidden="true">×</span></button>
      </header>

      <main className="mx-auto flex min-h-0 w-full max-w-[1440px] flex-1 flex-col items-center justify-center gap-3">
        <div className="flex w-full max-w-[min(100%,calc((100vh-13rem)*16/9))] items-center justify-between text-xs text-slate-300">
          <span>{kindLabel(slide.kind)}</span>
          <span aria-live="polite">Slide {slideIndex + 1} / {deck.slides.length}</span>
        </div>

        <section className={`w-full max-w-[min(100%,calc((100vh-13rem)*16/9))] overflow-hidden rounded-xl bg-white text-slate-950 shadow-2xl ${slide.kind === 'drawing_guide' ? 'teacher-deck-drawing-slide flex min-h-0 flex-1 flex-col sm:aspect-video sm:flex-none' : 'aspect-video'}`} style={slide.kind === 'drawing_guide' ? undefined : { aspectRatio: '16 / 9' }} aria-live="polite" aria-label={`Slide ${slideIndex + 1}: ${slide.title}`}>
          <div className="flex h-full flex-col p-[clamp(1rem,3.2vw,3.5rem)]">
            <div className="mb-4 flex shrink-0 items-center justify-between gap-4">
              <p className="text-[clamp(0.7rem,1.2vw,0.95rem)] font-bold uppercase tracking-[0.14em] text-blue-700">{deck.topic} · {deck.ageMonths} tháng</p>
              <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900">Bản nháp</span>
            </div>
            <h1 className="shrink-0 text-[clamp(1.5rem,3.1vw,3rem)] font-extrabold leading-tight tracking-tight">{slide.title}</h1>

            <div className={`mt-5 min-h-0 flex-1 text-[clamp(0.82rem,1.55vw,1.35rem)] leading-relaxed ${slide.kind === 'drawing_guide' ? 'overflow-y-auto overscroll-contain sm:overflow-hidden' : 'overflow-hidden'}`}>
              {slide.kind === 'orientation' && (
                <div className="flex h-full items-center">
                  <div className="w-full max-w-4xl">
                    <p className="mb-4 text-[0.78em] font-bold uppercase tracking-wide text-slate-500">Hôm nay chúng ta sẽ</p>
                    <TextList items={slide.bullets} emptyLabel="Cùng quan sát chủ đề và chia sẻ điều con nhận ra." />
                  </div>
                </div>
              )}

              {slide.kind === 'drawing_guide' && currentStep && (
                // Text and drawing sit side by side, so neither pushes the other off a projector screen.
                // Only the text area scrolls; the step buttons stay in place.
                <div className={`teacher-deck-guide grid h-full min-h-0 w-full min-w-0 gap-x-6 gap-y-3 ${showsDrawing ? 'sm:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]' : ''} sm:grid-rows-[minmax(0,1fr)]`}>
                  <div className="flex min-h-0 min-w-0 flex-col">
                    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain" data-testid="deck-step-text">
                      {/* Short steps sit in the middle of the column; long ones start at the top and scroll. */}
                      <div className="flex min-h-full flex-col justify-center">
                        <p className="text-[0.75em] font-bold uppercase tracking-wide text-slate-500">Bước {currentStep.stepIndex} / {slide.steps.length}</p>
                        <p className="mt-1 text-[1.3em] font-bold leading-snug">{currentStep.instruction}</p>
                        {currentStep.placement !== 'trên trang vẽ' && <p className="mt-2 text-[0.9em] text-slate-600">{currentStep.placement}</p>}
                        {!showsDrawing && <p className="mt-3 text-xs text-slate-600">Bài này chưa có hình vẽ mẫu. Giáo viên hướng dẫn trẻ theo từng bước bằng lời.</p>}
                      </div>
                    </div>
                    <div className="shrink-0 pt-2">
                    <div role="group" className="flex flex-wrap gap-2 py-1" aria-label="Chọn bước vẽ">
                      {slide.steps.map((step, index) => (
                        <button
                          key={step.stepIndex}
                          type="button"
                          onClick={() => setStepIndex(index)}
                          aria-label={`Bước ${step.stepIndex}`}
                          aria-current={index === stepIndex ? 'step' : undefined}
                          className={`!inline-flex !h-8 !min-h-8 !w-8 !min-w-8 shrink-0 !items-center !justify-center !rounded-full !border-2 !p-0 !text-xs font-bold leading-none transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 ${index === stepIndex ? '!border-blue-700 !bg-blue-700 !text-white' : '!border-slate-300 !bg-slate-100 !text-slate-900 hover:!bg-slate-200'}`}
                        >
                          <span aria-hidden="true">{step.stepIndex}</span>
                        </button>
                      ))}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
                      <button type="button" onClick={() => moveStep(-1)} disabled={stepIndex === 0} className="min-h-10 rounded-lg border border-slate-300 px-3 py-2 font-semibold disabled:opacity-40">Bước trước</button>
                      <button
                        type="button"
                        onClick={skipStep}
                        className="!min-h-10 !w-auto rounded-lg !px-3 !py-2 !text-sm font-semibold !bg-blue-700 !text-white transition hover:!bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
                      >
                        {nextStepLabel}
                      </button>
                    </div>
                    </div>
                  </div>
                  {showsDrawing && <TeacherProgressiveDrawing steps={slide.steps} currentStepIndex={stepIndex} title={slide.title} />}
                </div>
              )}

              {slide.kind === 'subject_exploration' && (
                <div className="flex h-full items-center">
                  <div className="w-full max-w-4xl"><TextList items={slide.bullets} emptyLabel="Cùng quan sát và nói về những gì mình nhìn thấy." /></div>
                </div>
              )}

              {slide.kind === 'approved_activity' && (
                <div className="grid h-full min-h-0 gap-x-8 gap-y-3 md:grid-cols-2">
                  <div className="min-h-0 space-y-4 overflow-y-auto overscroll-contain pr-2" tabIndex={0} aria-label="Mục tiêu, vật liệu và chuẩn bị hoạt động">
                    <section><h2 className="text-[0.72em] font-bold uppercase tracking-wide text-blue-700">Mục tiêu</h2><TextList items={slide.goal} emptyLabel="Quan sát và khám phá chủ đề." /></section>
                    <section><h2 className="text-[0.72em] font-bold uppercase tracking-wide text-blue-700">Vật liệu</h2><TextList items={slide.materials} emptyLabel="Theo phần chuẩn bị trong giáo án." /></section>
                    <section><h2 className="text-[0.72em] font-bold uppercase tracking-wide text-blue-700">Chuẩn bị</h2><TextList items={slide.preparation} emptyLabel="Giáo viên chuẩn bị trước hoạt động." /></section>
                  </div>
                  <div className="min-h-0 space-y-4 overflow-y-auto overscroll-contain pr-2" tabIndex={0} aria-label="Cách thực hiện và lưu ý an toàn">
                    <section><h2 className="text-[0.72em] font-bold uppercase tracking-wide text-blue-700">Cách thực hiện</h2><TextList items={slide.instructions} emptyLabel="Thực hiện theo kế hoạch đã duyệt." /></section>
                    {slide.safetyNotes.length > 0 && <section className="rounded-xl border border-amber-300 bg-amber-50 p-3"><h2 className="text-[0.72em] font-bold uppercase tracking-wide text-amber-900">Lưu ý an toàn</h2><TextList items={slide.safetyNotes} /></section>}
                  </div>
                </div>
              )}
            </div>
            <footer className="mt-4 flex shrink-0 items-center justify-between border-t border-slate-200 pt-3 text-xs text-slate-500">
              <span>{slideIndex + 1} / {deck.slides.length}</span>
              <span>Giáo viên hướng dẫn · trẻ vẽ bằng giấy và bút</span>
            </footer>
          </div>
        </section>

        <nav className="flex max-w-full items-center gap-2 overflow-x-auto py-1" aria-label="Chọn slide">
          {deck.slides.map((item, index) => <button key={item.slideIndex} type="button" onClick={() => selectSlide(index)} aria-current={index === slideIndex ? 'page' : undefined} aria-label={`Slide ${item.slideIndex}: ${item.title}`} className={`max-w-48 truncate rounded-lg border px-3 py-2 text-xs font-semibold ${index === slideIndex ? 'border-blue-400 bg-blue-500 text-white' : 'border-slate-600 text-slate-200 hover:bg-slate-800'}`}><span className="mr-1 opacity-70">{item.slideIndex}.</span>{item.title}</button>)}
        </nav>
      </main>

      <footer className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-3 pt-3">
        <button type="button" onClick={() => moveSlide(-1)} disabled={slideIndex === 0} className="rounded-lg border border-slate-500 px-4 py-2 text-sm font-semibold disabled:opacity-40">← Trước</button>
        <div className="hidden text-xs text-slate-400 sm:block">Dùng phím ← → để chuyển slide · Esc để đóng</div>
        <button type="button" onClick={() => moveSlide(1)} disabled={slideIndex === deck.slides.length - 1} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40">Tiếp →</button>
      </footer>
    </div>,
    document.body,
  )
}
