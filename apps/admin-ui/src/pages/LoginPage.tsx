import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import loginIllustration from '../assets/login-illustration.png'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    await new Promise((r) => setTimeout(r, 700))
    navigate('/')
    setLoading(false)
  }

  return (
    <div className="min-h-screen w-full flex bg-[#F0F8FF] relative overflow-hidden">
      {/* ── LEFT — Illustration panel ── */}
      <div className="flex-1 flex flex-col justify-between p-10 relative z-10">
        {/* Top left Logo */}
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 flex items-center justify-center">
              <svg viewBox="0 0 36 36" width="36" height="36" fill="none">
                <ellipse cx="12" cy="22" rx="9" ry="5" fill="#22C55E" transform="rotate(-30 12 22)"/>
                <path d="M18 6 C18 6 26 10 26 20 L18 28 L10 20 C10 10 18 6 18 6Z" fill="#2563EB"/>
                <circle cx="18" cy="17" r="3" fill="white" opacity="0.9"/>
                <path d="M15 28 Q18 34 21 28" fill="#F59E0B"/>
              </svg>
            </div>
            <span className="text-3xl font-extrabold text-blue-950 tracking-tight">Sketch2Life</span>
          </div>
          <div className="mt-3">
            <span className="inline-block bg-blue-100 text-blue-600 text-sm font-semibold px-4 py-1 rounded-full border border-blue-200/50">
              Cổng quản trị
            </span>
          </div>
        </div>

        {/* High-fidelity illustration from design */}
        <div className="w-full max-w-xl self-start mt-auto">
          <img
            src={loginIllustration}
            alt="Sketch2Life illustration"
            className="w-full h-auto object-contain pointer-events-none drop-shadow-sm"
          />
        </div>
      </div>

      {/* ── RIGHT — Floating login card ── */}
      <div className="flex-1 flex items-center justify-center p-8 relative z-10">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-gray-100/80 p-10">
          <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">Đăng nhập quản trị</h1>
          <p className="text-gray-500 text-sm text-center mb-8">
            Tài khoản người lớn được nhà trường cấp quyền.
          </p>

          <form onSubmit={handleLogin} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-gray-800 mb-1.5">Email</label>
              <div className="relative">
                <Mail size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@school.example"
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white text-gray-800"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-gray-800 mb-1.5">Mật khẩu</label>
              <div className="relative">
                <Lock size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-11 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition bg-white text-gray-800 tracking-wider"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3.5 rounded-xl transition text-[15px] shadow-sm active:scale-[0.99]"
            >
              {loading ? 'Đang xác thực...' : 'Đăng nhập'}
            </button>

            {/* Forgot password — aligned right matching design A00 */}
            <div className="text-right">
              <button
                type="button"
                className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
              >
                Quên mật khẩu?
              </button>
            </div>
          </form>

          {/* Footer note inside card */}
          <div className="flex items-center justify-center gap-2 mt-8 pt-6 border-t border-gray-100">
            <Lock size={15} className="text-gray-500 flex-shrink-0" />
            <p className="text-xs text-gray-500">
              Quyền truy cập được kiểm tra theo phạm vi và mục đích.
            </p>
          </div>
        </div>
      </div>

      {/* Watermark in bottom right */}
      <div className="absolute bottom-4 right-6 text-xs text-gray-400 pointer-events-none">
        Dữ liệu minh họa • Bản thiết kế UI.
      </div>
    </div>
  )
}
