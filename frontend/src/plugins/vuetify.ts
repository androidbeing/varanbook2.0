import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const varanTheme = {
  dark: false,
  colors: {
    primary: '#2196F3',       // Material Blue
    'on-primary': '#FFFFFF',  // white text on blue buttons
    secondary: '#1565C0',     // deeper blue complement
    accent: '#64B5F6',        // lighter blue accent
    error: '#D32F2F',
    warning: '#F57C00',
    info: '#0D47A1',
    success: '#43A047',
    surface: '#F3F8FF',       // very light blue tint
    background: '#EBF5FF',    // soft blue background
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
  },
})
