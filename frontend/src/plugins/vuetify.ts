import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const varanTheme = {
  dark: false,
  colors: {
    primary: '#B71C1C',       // deep red – auspicious
    secondary: '#F57F17',     // gold/amber
    accent: '#880E4F',        // deep pink
    error: '#D32F2F',
    warning: '#F57C00',
    info: '#1565C0',
    success: '#2E7D32',
    surface: '#FFFDE7',       // warm cream
    background: '#FFF8E1',
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
