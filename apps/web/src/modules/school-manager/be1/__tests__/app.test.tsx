import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from 'firebase/auth'
import App from '../App'
import { authService } from '../services/authService'
import { classService } from '../services/classService'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('School Manager BE1 authorization and connected class route', () => {
  let signedIn = false
  const user = { uid: 'admin-test' } as User

  beforeEach(() => {
    signedIn = false
    vi.spyOn(authService, 'observe').mockImplementation((callback) => {
      callback(signedIn ? user : null)
      return () => undefined
    })
    vi.spyOn(classService, 'currentAssignments').mockResolvedValue({
      contract: 'Be1AdultAssignmentsV1',
      assignments: [{ role: 'school_admin', class_id: null }],
    })
    vi.spyOn(classService, 'listClasses').mockResolvedValue([])
  })

  it('signs in with Firebase and verifies school_admin assignment before listing classes', async () => {
    const login = vi.spyOn(authService, 'login').mockImplementation(async () => {
      signedIn = true
      return user
    })
    render(<MemoryRouter initialEntries={['/school/login']}><App /></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.test' } })
    fireEvent.change(screen.getByLabelText('Mật khẩu'), { target: { value: 'test-password' } })
    fireEvent.submit(screen.getByLabelText('Email').closest('form')!)

    expect(await screen.findByRole('heading', { name: 'Lớp học' })).toBeTruthy()
    expect(login).toHaveBeenCalledWith({ email: 'admin@example.test', pass: 'test-password' })
    expect(classService.currentAssignments).toHaveBeenCalledOnce()
    expect(classService.listClasses).toHaveBeenCalledOnce()
  })

  it('does not render unsupported administration screens as if they were connected', async () => {
    signedIn = true
    render(<MemoryRouter initialEntries={['/school/users']}><App /></MemoryRouter>)

    expect(await screen.findByRole('heading', { name: 'Chức năng quản trị chưa nối BE1' })).toBeTruthy()
    expect(screen.queryByRole('heading', { name: 'Người dùng & vai trò' })).toBeNull()
  })
})