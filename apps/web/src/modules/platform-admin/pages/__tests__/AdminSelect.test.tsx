import { useState } from 'react'
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { AdminSelect } from '../../components/AdminSelect'

afterEach(cleanup)
function Sample() {
  const [value, setValue] = useState('teacher')
  return <AdminSelect aria-label='Vai trò' value={value} onChange={event => setValue(event.target.value)}>
    <option value='parent'>Phụ huynh</option><option value='teacher'>Giáo viên</option><option value='manager'>Quản lý trường</option>
  </AdminSelect>
}
describe('Admin select interaction', () => {
  it('changes with the keyboard and closes without changing on Escape', () => {
    render(<Sample />)
    const trigger = screen.getByRole('combobox', { name: 'Vai trò' })
    trigger.focus()
    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    fireEvent.keyDown(trigger, { key: 'Enter' })
    expect(trigger.textContent).toContain('Quản lý trường')
    expect(screen.queryByRole('listbox')).toBeNull()
    expect(document.activeElement).toBe(trigger)
    fireEvent.click(trigger)
    fireEvent.keyDown(trigger, { key: 'ArrowUp' })
    fireEvent.keyDown(trigger, { key: 'Escape' })
    expect(trigger.textContent).toContain('Quản lý trường')
    expect(screen.queryByRole('listbox')).toBeNull()
  })
  it('marks the current option and dismisses when clicking outside', () => {
    render(<Sample />)
    fireEvent.click(screen.getByRole('combobox'))
    expect(screen.getByRole('option', { name: 'Giáo viên' }).getAttribute('aria-selected')).toBe('true')
    fireEvent.click(screen.getByRole('option', { name: 'Phụ huynh' }))
    expect(screen.getByRole('combobox').textContent).toContain('Phụ huynh')
    fireEvent.click(screen.getByRole('combobox'))
    fireEvent.pointerDown(document.body)
    expect(screen.queryByRole('listbox')).toBeNull()
  })
})
