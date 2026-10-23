import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import loginIllustration from '../assets/login-illustration.png'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('••••••••')
  const [showPw, setShowPw] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/')
  }

  return (
    <div className="h-screen w-full flex bg-[#F9FBFD] overflow-hidden select-none">
      {/* ── LEFT PANEL ── */}
      <div className="w-[43.5%] min-w-[480px] bg-[#D9F1FE] flex flex-col justify-between relative overflow-hidden">
        <div className="pt-11 px-13 z-10">
          {/* Brand Logo with 3 yellow rays */}
          <div className="inline-flex items-start">
            <span className="text-[36px] font-extrabold tracking-tight leading-none text-[#0B2545]">
              Sketch<span className="text-[#1D63F2]">2</span>Life
            </span>
            <svg
              width="24"
              height="28"
              viewBox="0 0 24 28"
              fill="none"
              className="-ml-0.5 -mt-2"
            >
              <line x1="5" y1="9" x2="9" y2="2" stroke="#F59E0B" strokeWidth="3.5" strokeLinecap="round" />
              <line x1="11" y1="14" x2="19" y2="10" stroke="#F59E0B" strokeWidth="3.5" strokeLinecap="round" />
              <line x1="11" y1="21" x2="19" y2="22" stroke="#F59E0B" strokeWidth="3.5" strokeLinecap="round" />
            </svg>
          </div>

          {/* Role badge */}
          <div className="mt-3.5">
            <span className="inline-block bg-[#C7E6FD] text-[#1D63F2] text-[15px] font-semibold px-5 py-1.5 rounded-full">
              Dành cho giáo viên
            </span>
          </div>

          {/* Headline */}
          <h1 className="mt-7 text-[40px] font-extrabold text-[#0A1F33] leading-[1.22] tracking-tight">
            Cùng trẻ khám phá,
            <br />
            sáng tạo và hợp tác
          </h1>

          {/* Subtitle */}
          <p className="mt-3.5 text-[17.5px] text-[#334E68] font-normal">
            Điều phối lớp học <span className="mx-1">•</span> Đồng hành cùng từng trẻ
          </p>
        </div>

        {/* Bottom Illustration */}
        <div className="w-full mt-auto">
          <img
            src={loginIllustration}
            alt="Sketch2Life Teacher Illustration"
            className="w-full h-auto block object-cover pointer-events-none"
          />
        </div>
      </div>

      {/* ── RIGHT PANEL ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#F9FBFD]">
        <div className="w-full max-w-[468px] bg-white rounded-[24px] shadow-[0_12px_40px_rgba(15,23,42,0.06)] border border-slate-100 px-10 py-11">
          <h2 className="text-[28px] font-extrabold text-[#0F172A] text-center tracking-tight">
            Đăng nhập giáo viên
          </h2>
          <p className="text-[15px] text-slate-500 text-center mt-2 mb-8">
            Sử dụng tài khoản do nhà trường cấp
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-[14px] font-semibold text-[#0F172A] mb-2">
                Email
              </label>
              <div className="relative">
                <Mail
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email của bạn"
                  className="w-full pl-11 pr-4 py-3.5 border border-slate-200 rounded-xl text-[14.5px] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1D63F2] focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-[14px] font-semibold text-[#0F172A] mb-2">
                Mật khẩu
              </label>
              <div className="relative">
                <Lock
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-11 py-3.5 border border-slate-200 rounded-xl text-[15px] text-slate-800 tracking-widest focus:outline-none focus:ring-2 focus:ring-[#1D63F2] focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPw ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              className="w-full bg-[#1D63F2] hover:bg-[#1554D6] text-white font-semibold py-3.5 rounded-xl text-[16px] shadow-sm transition cursor-pointer mt-1"
            >
              Đăng nhập
            </button>

            {/* Forgot password */}
            <div className="text-right pt-0.5">
              <button
                type="button"
                className="text-[#1D63F2] hover:underline text-[14px] font-semibold"
              >
                Quên mật khẩu?
              </button>
            </div>
          </form>

          {/* Footer info */}
          <div className="mt-7 pt-6 border-t border-slate-100 text-center space-y-1.5">
            <p className="text-[13px] text-slate-500">
              Chỉ giáo viên được phân công mới có quyền truy cập lớp học.
            </p>
            <div>
              <button
                type="button"
                className="text-[13px] text-[#1D63F2] underline font-medium hover:text-blue-800"
              >
                Cần hỗ trợ từ nhà trường?
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
