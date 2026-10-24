import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { User } from 'firebase/auth'
import App from '../App'
import { authService } from '../services/authService'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Teacher UI authentication boundary', () => {
  let signedIn = false
  const user = { uid: 'teacher-test' } as User

  beforeEach(() => {
    signedIn = false
    window.history.replaceState({}, '', '/login')
    vi.spyOn(authService, 'observe').mockImplementation((callback) => {
      callback(signedIn ? user : null)
      return () => undefined
    })
  })

  it('authenticates with Firebase before opening teacher routes', async () => {
    const login = vi.spyOn(authService, 'login').mockImplementation(async () => {
      signedIn = true
      return user
    })

    render(<App />)
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'teacher@example.test' } })
    fireEvent.change(screen.getByLabelText('Mật khẩu'), { target: { value: 'test-password' } })
    fireEvent.submit(screen.getByLabelText('Email').closest('form')!)

    expect(await screen.findByRole('heading', { name: 'Trang tổng quan chưa được nối BE1/BE2' })).toBeTruthy()
    expect(login).toHaveBeenCalledWith({ email: 'teacher@example.test', pass: 'test-password' })
  })

  it('keeps protected routes closed while signed out', async () => {
    window.history.replaceState({}, '', '/')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Đăng nhập giáo viên' })).toBeTruthy()
  })

  it('shows fixture dashboards only when demo mode is explicitly requested', async () => {
    signedIn = true
    window.history.replaceState({}, '', '/?demo=1')
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Chào cô/thầy' })).toBeTruthy()
  })
})
