import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'

const sparklePositions = [
  'sparkle--left',
  'sparkle--right',
  'sparkle--top',
  'sparkle--bottom',
]

export default function SplashScreen() {
  const rootRef = useRef(null)

  useEffect(() => {
    const root = rootRef.current
    if (!root) return undefined

    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

    const context = gsap.context(() => {
      const background = root.querySelector('[data-splash-background]')
      const logo = root.querySelector('[data-splash-logo]')
      const pencil = root.querySelector('[data-splash-pencil]')
      const sparkles = root.querySelectorAll('[data-splash-sparkle]')

      if (reducedMotion) {
        gsap.set([background, logo, pencil, ...sparkles], {
          autoAlpha: 1,
          clearProps: 'transform',
        })

        return
      }

      const timeline = gsap.timeline()

      timeline
        .set(background, { autoAlpha: 1 })
        .fromTo(
          pencil,
          {
            autoAlpha: 0,
            xPercent: -50,
            yPercent: -50,
            y: '28vh',
            rotation: -10,
            scale: 0.88,
          },
          {
            autoAlpha: 1,
            xPercent: -50,
            yPercent: -50,
            y: 0,
            rotation: 3,
            scale: 1,
            duration: 0.84,
            ease: 'elastic.out(1, 0.55)',
          },
          0.08,
        )
        .fromTo(
          logo,
          {
            autoAlpha: 0,
            xPercent: -50,
            y: -14,
            scale: 0.8,
          },
          {
            autoAlpha: 1,
            xPercent: -50,
            y: 0,
            scale: 1,
            duration: 0.52,
            ease: 'back.out(1.55)',
          },
          0.38,
        )
        .fromTo(
          sparkles,
          {
            autoAlpha: 0,
            scale: 0.25,
            rotation: -28,
          },
          {
            autoAlpha: 0.9,
            scale: 1,
            rotation: 0,
            duration: 0.24,
            stagger: 0.05,
            ease: 'back.out(2.4)',
          },
          0.74,
        )
        .to(
          pencil,
          {
            y: -7,
            rotation: 1.5,
            duration: 0.34,
            repeat: 2,
            yoyo: true,
            ease: 'sine.inOut',
          },
          1.02,
        )
    }, root)

    return () => context.revert()
  }, [])

  return (
    <main ref={rootRef} className="splash-screen" aria-label="Đang tải Sketch2Life" role="status">
      <img
        className="splash-screen__background"
        src="/assets/splash/background.png"
        alt=""
        aria-hidden="true"
        data-splash-background
      />

      <div className="splash-screen__art" aria-hidden="true">
        <img
          className="splash-screen__logo"
          src="/assets/splash/logo.png"
          alt=""
          data-splash-logo
        />

        <img
          className="splash-screen__pencil"
          src="/assets/splash/pencil.png"
          alt=""
          data-splash-pencil
        />

        {sparklePositions.map((position) => (
          <span
            className={`splash-screen__sparkle ${position}`}
            data-splash-sparkle
            key={position}
          />
        ))}
      </div>
    </main>
  )
}
