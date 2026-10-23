import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail } from 'lucide-react'
import loginBg from '../assets/login-bg.png'
import loginLogoIcon from '../assets/login-logo-icon.png'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('••••••••')
  const [showPass, setShowPass] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    navigate('/')
  }

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#F8FCFE] select-none">
      {/* Full background illustration matching A00-dang-nhap.png */}
      <img
        src={loginBg}
        alt="Sketch2Life Admin Login"
        className="absolute inset-0 w-full h-full object-cover object-left-bottom pointer-events-none"
      />

      {/* Left brand header: Sketch2Life + centered "Cổng quản trị" badge */}
      <div className="absolute top-0 left-0 w-[46%] pt-10 lg:pt-12 flex flex-col items-center justify-center z-10 pointer-events-none">
        <div className="flex items-center justify-center gap-3">
          <img
            src={loginLogoIcon}
            alt="Sketch2Life Icon"
            className="w-12 h-12 object-contain shrink-0"
          />
          <span className="text-[38px] font-extrabold tracking-tight leading-none text-[#0B2240]">
            Sketch<span className="text-[#1565F9]">2</span>Life
          </span>
        </div>
        <div className="mt-3 flex justify-center w-full">
          <span className="inline-flex items-center justify-center bg-[#C2E7FF] text-[#1565F9] text-[15px] font-bold px-6 py-1.5 rounded-full whitespace-nowrap">
            Cổng quản trị
          </span>
        </div>
      </div>

      {/* Right login card positioned to match A00-dang-nhap.png */}
      <div className="relative z-10 w-full h-full flex items-center justify-end pr-[5.8%] lg:pr-[6.2%]">
        <div className="w-[584px] max-w-[90vw] bg-white rounded-[24px] shadow-[0_12px_40px_rgba(15,41,66,0.06)] border border-slate-100/80 px-10 py-10 flex flex-col justify-between min-h-[650px]">
          <div className="my-auto">
            {/* Heading */}
            <div className="text-center mb-9">
              <h1 className="text-[34px] font-extrabold text-[#0F1F38] tracking-tight">
                Đăng nhập quản trị
              </h1>
              <p className="text-[16px] text-slate-500 mt-2.5 font-medium">
                Tài khoản người lớn được nhà trường cấp quyền.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email */}
              <div>
                <label className="block text-[15px] font-bold text-slate-800 mb-2">
                  Email
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                    <Mail size={20} strokeWidth={1.8} />
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@school.example"
                    className="w-full pl-12 pr-4 py-3.5 border border-slate-200 rounded-xl text-[16px] text-slate-700 placeholder-slate-400 bg-[#FAFBFD] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-[15px] font-bold text-slate-800 mb-2">
                  Mật khẩu
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                    <Lock size={20} strokeWidth={1.8} />
                  </span>
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-12 py-3.5 border border-slate-200 rounded-xl text-[16px] text-slate-800 tracking-widest bg-[#FAFBFD] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((v) => !v)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPass ? <EyeOff size={21} /> : <Eye size={21} />}
                  </button>
                </div>
              </div>

              {/* Submit */}
              <div className="pt-1">
                <button
                  type="submit"
                  className="w-full bg-[#1565F9] hover:bg-blue-700 text-white font-bold py-4 rounded-2xl text-[17px] transition-colors shadow-[0_4px_14px_rgba(21,101,249,0.28)] cursor-pointer"
                >
                  Đăng nhập
                </button>
              </div>

              {/* Forgot password */}
              <div className="text-right pt-0.5">
                <button
                  type="button"
                  className="text-[15px] text-[#1565F9] hover:underline font-semibold"
                >
                  Quên mật khẩu?
                </button>
              </div>
            </form>

            {/* Footer note */}
            <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-2.5 text-[14px] text-slate-500 font-medium">
              <Lock size={16} className="text-slate-400 flex-shrink-0" />
              <span>Quyền truy cập được kiểm tra theo phạm vi và mục đích.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
