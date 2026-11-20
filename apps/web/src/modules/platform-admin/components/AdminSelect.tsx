import { Children, isValidElement, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Check, ChevronDown } from 'lucide-react'

type Option = { value: string; label: ReactNode; disabled?: boolean }
type Props = {
  value: string | number; onChange: (event: { target: { value: string } }) => void
  children: ReactNode; id?: string; disabled?: boolean; required?: boolean; 'aria-label'?: string
}

// Native form validation is retained; the visible combobox owns keyboard focus.
export function AdminSelect({ value, onChange, children, id, disabled, required, 'aria-label': ariaLabel }: Props) {
  const generated = useId(), listId = generated + '-list'
  const trigger = useRef<HTMLButtonElement>(null), popup = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false), [active, setActive] = useState(0)
  const [position, setPosition] = useState({ left: 0, top: 0, width: 0, maxHeight: 280 })
  const search = useRef({ text: '', at: 0 })
  const options: Option[] = []
  const collect = (nodes: ReactNode) => Children.forEach(nodes, node => {
    if (!isValidElement<{ value?: string; disabled?: boolean; children?: ReactNode }>(node)) return
    if (node.type === 'option') options.push({ value: String(node.props.value ?? ''), label: node.props.children, disabled: node.props.disabled })
    else collect(node.props.children)
  })
  collect(children)
  const selected = Math.max(0, options.findIndex(option => option.value === String(value)))
  function reveal() { if (!disabled) { setActive(selected); setOpen(true) } }
  function choose(index: number) {
    const option = options[index]
    if (!option || option.disabled) return
    onChange({ target: { value: option.value } }); setOpen(false); trigger.current?.focus()
  }
  function move(direction: number) {
    let next = active
    for (let count = 0; count < options.length; count++) {
      next = (next + direction + options.length) % options.length
      if (!options[next].disabled) { setActive(next); break }
    }
  }
  useLayoutEffect(() => {
    if (!open) return
    const place = () => {
      const rect = trigger.current?.getBoundingClientRect()
      if (!rect) return
      const roomBelow = window.innerHeight - rect.bottom - 12
      const height = Math.min(280, Math.max(roomBelow, rect.top - 12))
      const above = roomBelow < 180 && rect.top > roomBelow
      setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8)), top: above ? Math.max(8, rect.top - Math.min(height, options.length * 42 + 12) - 6) : rect.bottom + 6, width: rect.width, maxHeight: height })
    }
    const outside = (event: PointerEvent) => {
      if (!trigger.current?.contains(event.target as Node) && !popup.current?.contains(event.target as Node)) setOpen(false)
    }
    place()
    window.addEventListener('resize', place); window.addEventListener('scroll', place, true)
    document.addEventListener('pointerdown', outside)
    return () => { window.removeEventListener('resize', place); window.removeEventListener('scroll', place, true); document.removeEventListener('pointerdown', outside) }
  }, [open, options.length])
  useLayoutEffect(() => { if (open) document.getElementById(listId + '-' + active)?.scrollIntoView?.({ block: 'nearest' }) }, [open, active, listId])
  return <>
    <select className='pa-select-native' hidden aria-hidden='true' tabIndex={-1} value={value} required={required} disabled={disabled} onChange={onChange} onInvalid={event => { event.preventDefault(); trigger.current?.focus() }}>{children}</select>
    <button id={id ?? generated + '-trigger'} ref={trigger} type='button' role='combobox' className='pa-select-trigger' aria-label={ariaLabel} aria-required={required} aria-haspopup='listbox' aria-expanded={open} aria-controls={open ? listId : undefined} aria-activedescendant={open ? listId + '-' + active : undefined} disabled={disabled}
      onClick={() => open ? setOpen(false) : reveal()}
      onBlur={event => { if (!popup.current?.contains(event.relatedTarget as Node)) setOpen(false) }}
      onKeyDown={event => {
        if (event.key === 'Tab') { setOpen(false); return }
        if (event.key === 'Escape') { event.preventDefault(); setOpen(false); return }
        if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' '].includes(event.key)) {
          event.preventDefault()
          if (!open) { reveal(); return }
          if (event.key === 'Enter' || event.key === ' ') choose(active)
          else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') move(event.key === 'ArrowDown' ? 1 : -1)
          else setActive(event.key === 'Home' ? 0 : options.length - 1)
        } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
          const now = Date.now(); search.current.text = (now - search.current.at > 700 ? '' : search.current.text) + event.key.toLocaleLowerCase('vi-VN'); search.current.at = now
          const found = options.findIndex(option => !option.disabled && String(option.label).toLocaleLowerCase('vi-VN').startsWith(search.current.text))
          if (found >= 0) { setOpen(true); setActive(found) }
        }
      }}><span>{options[selected]?.label}</span><ChevronDown size={16} aria-hidden='true' /></button>
    {open && createPortal(<div ref={popup} id={listId} role='listbox' aria-label={ariaLabel} aria-labelledby={ariaLabel ? undefined : id ?? generated + '-trigger'} className='pa-select-menu' style={position}>
      {options.map((option, index) => <div key={option.value} id={listId + '-' + index} role='option' aria-selected={option.value === String(value)} aria-disabled={option.disabled} className={'pa-select-option' + (active === index ? ' is-highlighted' : '')} onPointerMove={() => { if (!option.disabled) setActive(index) }} onPointerDown={event => event.preventDefault()} onClick={() => choose(index)}><span>{option.label}</span>{option.value === String(value) && <Check size={16} aria-hidden='true' />}</div>)}
    </div>, document.body)}
  </>
}
