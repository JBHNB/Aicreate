<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  color: string
}

const canvasRef = ref<HTMLCanvasElement | null>(null)

let animationId = 0
let particles: Particle[] = []
let width = 0
let height = 0
let dpr = 1
let particleCount = 45
let lastFrameTime = 0
let frameSkip = 0
let isPaused = false
let isInteracting = false
let interactTimer: ReturnType<typeof setTimeout> | null = null

const LINK_DISTANCE = 110
const LINK_DISTANCE_SQ = LINK_DISTANCE * LINK_DISTANCE
const FRAME_INTERVAL = 1000 / 30 // 30 FPS
const PARTICLE_COLORS = [
  'rgba(34, 211, 238, 0.75)',
  'rgba(34, 197, 94, 0.7)',
  'rgba(129, 140, 248, 0.65)',
]

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min)
}

function resolveParticleCount(w: number, h: number) {
  const area = w * h
  if (area < 500_000) return 28
  if (area < 900_000) return 38
  return 45
}

function createParticle(): Particle {
  return {
    x: randomBetween(0, width),
    y: randomBetween(0, height),
    vx: randomBetween(-0.28, 0.28),
    vy: randomBetween(-0.28, 0.28),
    size: randomBetween(1, 2),
    opacity: randomBetween(0.35, 0.8),
    color: PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
  }
}

function initParticles() {
  particleCount = resolveParticleCount(width, height)
  particles = Array.from({ length: particleCount }, createParticle)
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  const parent = canvas.parentElement
  if (!parent) return

  dpr = Math.min(window.devicePixelRatio || 1, 1.25)
  width = parent.clientWidth
  height = parent.clientHeight
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`

  initParticles()
}

function drawLinks(ctx: CanvasRenderingContext2D) {
  const cellSize = LINK_DISTANCE
  const cols = Math.ceil(width / cellSize) || 1
  const rows = Math.ceil(height / cellSize) || 1
  const buckets: number[][] = Array.from({ length: cols * rows }, () => [])

  for (let i = 0; i < particles.length; i += 1) {
    const p = particles[i]
    const col = Math.min(cols - 1, Math.max(0, Math.floor(p.x / cellSize)))
    const row = Math.min(rows - 1, Math.max(0, Math.floor(p.y / cellSize)))
    buckets[row * cols + col].push(i)
  }

  ctx.lineWidth = 0.5
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const cell = buckets[row * cols + col]
      if (cell.length === 0) continue

      for (let ni = -1; ni <= 1; ni += 1) {
        for (let nj = -1; nj <= 1; nj += 1) {
          const nbRow = row + ni
          const nbCol = col + nj
          if (nbRow < 0 || nbRow >= rows || nbCol < 0 || nbCol >= cols) continue

          const neighborCell = buckets[nbRow * cols + nbCol]
          for (const i of cell) {
            for (const j of neighborCell) {
              if (j <= i) continue
              const a = particles[i]
              const b = particles[j]
              const dx = a.x - b.x
              const dy = a.y - b.y
              const distSq = dx * dx + dy * dy
              if (distSq > LINK_DISTANCE_SQ) continue

              const alpha = (1 - Math.sqrt(distSq) / LINK_DISTANCE) * 0.18
              ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`
              ctx.beginPath()
              ctx.moveTo(a.x, a.y)
              ctx.lineTo(b.x, b.y)
              ctx.stroke()
            }
          }
        }
      }
    }
  }
}

function drawFrame(timestamp: number) {
  animationId = window.requestAnimationFrame(drawFrame)

  if (isPaused) return

  const interval = isInteracting ? FRAME_INTERVAL * 2 : FRAME_INTERVAL
  if (timestamp - lastFrameTime < interval) return
  lastFrameTime = timestamp

  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d', { alpha: true })
  if (!ctx) return

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)

  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 0 || p.x > width) p.vx *= -1
    if (p.y < 0 || p.y > height) p.vy *= -1

    ctx.globalAlpha = p.opacity
    ctx.fillStyle = p.color
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  frameSkip = (frameSkip + 1) % 2
  if (!isInteracting && frameSkip === 0) {
    drawLinks(ctx)
  }
}

function onVisibilityChange() {
  isPaused = document.hidden
  if (!isPaused) {
    lastFrameTime = 0
  }
}

function onPointerDown() {
  isInteracting = true
  if (interactTimer) clearTimeout(interactTimer)
  interactTimer = setTimeout(() => {
    isInteracting = false
  }, 500)
}

function startAnimation() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  cancelAnimationFrame(animationId)
  lastFrameTime = 0
  animationId = window.requestAnimationFrame(drawFrame)
}

function stopAnimation() {
  cancelAnimationFrame(animationId)
}

onMounted(() => {
  resizeCanvas()
  startAnimation()
  window.addEventListener('resize', resizeCanvas, { passive: true })
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('pointerdown', onPointerDown, { passive: true, capture: true })
})

onBeforeUnmount(() => {
  stopAnimation()
  window.removeEventListener('resize', resizeCanvas)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  window.removeEventListener('pointerdown', onPointerDown, { capture: true })
  if (interactTimer) clearTimeout(interactTimer)
})
</script>

<template>
  <canvas ref="canvasRef" class="tech-particle-canvas" aria-hidden="true" />
</template>

<style scoped>
.tech-particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  contain: strict;
}
</style>
