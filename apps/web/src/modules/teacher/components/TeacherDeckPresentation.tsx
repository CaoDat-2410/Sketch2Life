import { useEffect, useMemo, useState } from 'react'

type SlideKind = 'orientation' | 'drawing_guide' | 'subject_exploration' | 'approved_activity'

type DrawingStep = Readonly<{
  stepIndex: number
  instruction: string
  placement: string
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
  visualBase64: string | null
  visualBusy: boolean
  visualError: string
  onGenerateVisual: () => void
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
      if (!Array.isArray(item.steps) || item.steps.length < 3 || item.steps.length > 5) return null
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
  visualBase64,
  visualBusy,
  visualError,
  onGenerateVisual,
  onClose,
}: Props) {
  const [slideIndex, setSlideIndex] = useState(0)
  const [stepIndex, setStepIndex] = useState(0)
  const slide = deck.slides[slideIndex]
  const currentStep = slide.kind === 'drawing_guide' ? slide.steps[stepIndex] : null
  const imageSrc = useMemo(
    () => visualBase64 && /^[A-Za-z0-9+/]+={0,2}$/.test(visualBase64) ? `data:image/png;base64,${visualBase64}` : null,
    [visualBase64],
  )

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

  return (
    <div className="fixed inset-0 z-[100] flex flex-col bg-slate-950 p-3 text-white sm:p-5" role="dialog" aria-modal="true" aria-label="Trình chiếu Sketch Deck">
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

        <section className="w-full max-w-[min(100%,calc((100vh-13rem)*16/9))] overflow-hidden rounded-xl bg-white text-slate-950 shadow-2xl" style={{ aspectRatio: '16 / 9' }} aria-live="polite" aria-label={`Slide ${slideIndex + 1}: ${slide.title}`}>
          <div className="flex h-full flex-col p-[clamp(1rem,3.2vw,3.5rem)]">
            <div className="mb-4 flex shrink-0 items-center justify-between gap-4">
              <p className="text-[clamp(0.7rem,1.2vw,0.95rem)] font-bold uppercase tracking-[0.14em] text-blue-700">{deck.topic} · {deck.ageMonths} tháng</p>
              <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900">Bản nháp</span>
            </div>
            <h1 className="shrink-0 text-[clamp(1.5rem,3.1vw,3rem)] font-extrabold leading-tight tracking-tight">{slide.title}</h1>

            <div className="mt-5 min-h-0 flex-1 overflow-hidden text-[clamp(0.82rem,1.55vw,1.35rem)] leading-relaxed">
              {slide.kind === 'orientation' && (
                <div className="flex h-full items-center">
                  <div className="w-full max-w-4xl">
                    <p className="mb-4 text-[0.78em] font-bold uppercase tracking-wide text-slate-500">Hôm nay chúng ta sẽ</p>
                    <TextList items={slide.bullets} emptyLabel="Cùng quan sát chủ đề và chia sẻ điều con nhận ra." />
                  </div>
                </div>
              )}

              {slide.kind === 'drawing_guide' && currentStep && (
                <div className="grid h-full min-h-0 gap-5 lg:grid-cols-[0.82fr_1.18fr]">
                  <div className="flex min-h-0 flex-col justify-center">
                    <p className="text-[0.75em] font-bold uppercase tracking-wide text-slate-500">Bước {currentStep.stepIndex} / {slide.steps.length}</p>
                    <p className="mt-2 text-[1.35em] font-bold leading-snug">{currentStep.instruction}</p>
                    <p className="mt-3 text-[0.85em] text-slate-600">{currentStep.placement}</p>
                    <div className="mt-5 flex flex-wrap gap-2" aria-label="Chọn bước vẽ">
                      {slide.steps.map((step, index) => <button key={step.stepIndex} type="button" onClick={() => setStepIndex(index)} aria-label={`Mở bước vẽ ${step.stepIndex}`} aria-current={index === stepIndex ? 'step' : undefined} className={`h-3 w-8 rounded-full ${index === stepIndex ? 'bg-blue-700' : 'bg-slate-300 hover:bg-slate-400'}`} />)}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-sm">
                      <button type="button" onClick={() => moveStep(-1)} disabled={stepIndex === 0} className="rounded-lg border border-slate-300 px-3 py-2 font-semibold disabled:opacity-40">Bước trước</button>
                      <button type="button" onClick={skipStep} className="rounded-lg bg-blue-700 px-3 py-2 font-semibold text-white hover:bg-blue-800">Bỏ qua bước</button>
                    </div>
                  </div>
                  <div className="flex min-h-0 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white p-2">
                    {imageSrc
                      ? <img src={imageSrc} alt={`Hướng dẫn line-sketch ${deck.topic}, gồm ${slide.steps.length} bước`} className="max-h-full max-w-full object-contain" />
                      : <div className="max-w-sm px-5 text-center">
                          <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-full bg-blue-50 text-2xl text-blue-700" aria-hidden="true">✎</div>
                          <p className="font-bold">Chưa có hình hướng dẫn</p>
                          <p className="mt-1 text-sm text-slate-600">Tạo ảnh line-sketch tùy chọn để hiển thị cùng các bước vẽ.</p>
                          {visualError && <p role="alert" className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-800">{visualError}</p>}
                          <button type="button" disabled={visualBusy} onClick={onGenerateVisual} className="mt-4 rounded-lg bg-blue-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-60">{visualBusy ? 'Đang tạo ảnh…' : 'Tạo ảnh hướng dẫn'}</button>
                        </div>}
                  </div>
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
    </div>
  )
}
