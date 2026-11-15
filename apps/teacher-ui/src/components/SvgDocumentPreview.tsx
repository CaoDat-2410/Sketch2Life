import type { SvgDocumentV1 } from '../domain/svgGuide'

type Props = Readonly<{
  document: SvgDocumentV1
  title: string
  altText: string
}>

export function SvgDocumentPreview({ document, title, altText }: Props) {
  return (
    <figure className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <figcaption className="mb-3 text-sm font-semibold text-slate-700">{title}</figcaption>
      <div className="mx-auto aspect-square w-full max-w-[560px] overflow-hidden rounded-xl border border-slate-100 bg-[#fffdf7] p-4">
        <svg
          viewBox={document.view_box}
          role="img"
          aria-label={altText}
          className="h-full w-full"
          data-testid="svg-document-preview"
        >
          {document.paths.map((path) => (
            <path
              key={path.path_id}
              d={path.d}
              fill={path.fill}
              stroke={path.stroke}
              strokeWidth={path.stroke_width}
              strokeLinecap="round"
              strokeLinejoin="round"
              data-path-id={path.path_id}
            />
          ))}
        </svg>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{altText}</p>
    </figure>
  )
}
