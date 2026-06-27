import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Base surfaces
        void:    '#0A0F1E',   // deep night — main background
        surface: '#111827',   // card/panel background
        overlay: '#1F2937',   // elevated surfaces, dropdowns
        border:  '#374151',   // subtle borders
        // Text
        primary:   '#F9FAFB', // primary text
        secondary: '#9CA3AF', // muted labels
        tertiary:  '#6B7280', // placeholders, disabled
        // Brand accent
        accent:  '#3B82F6',   // electric blue — primary actions
        'accent-hover': '#2563EB',
        // Status — transaction states
        processed: '#10B981', // emerald green
        pending:   '#F59E0B', // amber
        failed:    '#EF4444', // red
        // WS event stream colours
        'event-created': '#60A5FA',
        'event-changed': '#34D399',
        'event-ping':    '#6B7280',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      animation: {
        'slide-in':    'slideIn 0.25s ease-out',
        'fade-in':     'fadeIn 0.2s ease-out',
        'pulse-dot':   'pulseDot 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'spin-slow':   'spin 3s linear infinite',
      },
      keyframes: {
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.3' },
        },
      },
      boxShadow: {
        'glow-accent':    '0 0 20px rgba(59,130,246,0.15)',
        'glow-processed': '0 0 12px rgba(16,185,129,0.2)',
      },
    },
  },
  plugins: [],
} satisfies Config
