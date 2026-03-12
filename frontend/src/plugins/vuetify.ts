import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const varanTheme = {
  dark: false,
  colors: {
    primary: '#1E88E5',         // Blue 600 — elevated, richer
    'on-primary': '#FFFFFF',
    secondary: '#1565C0',       // Blue 800 — deep contrast
    accent: '#EC407A',          // Pink 400 — romantic rose accent
    'on-accent': '#FFFFFF',
    error: '#D32F2F',
    warning: '#F57C00',
    info: '#0D47A1',
    success: '#2E7D32',         // Green 800 — richer success
    surface: '#F7F9FF',         // cooler, cleaner surface
    background: '#EDF3FF',      // soft blue background
  },
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'varanTheme',
    themes: { varanTheme },
  },
  defaults: {
    VBtn: { style: 'text-transform: none;' },
    VCard: { rounded: 'lg' },
    VChip: { class: 'ma-1' },
  },
})
