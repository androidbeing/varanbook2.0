<template>
  <v-app>
    <!-- ── Top App Bar ─────────────────────────────────────────────────── -->
    <v-app-bar flat color="transparent" class="px-2 px-sm-4">
      <v-app-bar-title>
        <span class="text-h5 font-weight-bold text-primary landing-brand">Varanbook</span>
      </v-app-bar-title>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        rounded="lg"
        size="default"
        class="text-none font-weight-medium"
        :to="{ name: 'login' }"
      >
        <v-icon start>mdi-login</v-icon>
        Login
      </v-btn>
    </v-app-bar>

    <v-main class="bg-background">
      <!-- ── Hero Section ────────────────────────────────────────────── -->
      <section class="landing-hero">
        <v-container>
          <v-row align="center" justify="center">
            <v-col cols="12" md="7" class="text-center text-md-start">
              <h1 class="landing-headline text-primary mb-4">
                Manage Your Matrimonial Centre — <span class="text-accent">Effortlessly</span>
              </h1>
              <p class="landing-subtext text-medium-emphasis mb-6">
                Varanbook is a modern platform built exclusively for <strong>matrimonial information centres</strong>.
                Digitise profiles, manage memberships, share shortlists, and delight families — all from one place.
              </p>
              <div class="d-flex flex-column flex-sm-row ga-3 justify-center justify-md-start">
                <v-btn
                  color="primary"
                  size="x-large"
                  rounded="lg"
                  class="text-none font-weight-medium"
                  href="https://wa.me/919944926396?text=Hi%2C%20I%20want%20to%20onboard%20my%20matrimonial%20centre%20on%20Varanbook"
                  target="_blank"
                  rel="noopener"
                >
                  <v-icon start>mdi-whatsapp</v-icon>
                  Get Started on WhatsApp
                </v-btn>
                <v-btn
                  variant="outlined"
                  color="primary"
                  size="x-large"
                  rounded="lg"
                  class="text-none font-weight-medium"
                  :to="{ name: 'login' }"
                >
                  Already onboarded? Login
                </v-btn>
              </div>
            </v-col>
            <v-col cols="12" md="5" class="text-center d-none d-md-flex justify-center">
              <v-icon color="primary" size="260" class="landing-hero-icon">mdi-account-heart</v-icon>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── Features Section ────────────────────────────────────────── -->
      <section class="landing-features py-12 py-md-16">
        <v-container>
          <h2 class="text-h4 font-weight-bold text-center mb-2">Why Centres Love Varanbook</h2>
          <p class="text-body-1 text-medium-emphasis text-center mb-10" style="max-width: 600px; margin: 0 auto;">
            Purpose-built tools that save time, impress families, and grow your business.
          </p>

          <v-row justify="center">
            <v-col v-for="feature in features" :key="feature.title" cols="12" sm="6" md="4">
              <v-card flat rounded="xl" class="pa-6 text-center feature-card fill-height">
                <v-icon :color="feature.color" size="48" class="mb-4">{{ feature.icon }}</v-icon>
                <h3 class="text-h6 font-weight-semibold mb-2">{{ feature.title }}</h3>
                <p class="text-body-2 text-medium-emphasis">{{ feature.desc }}</p>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── How It Works ────────────────────────────────────────────── -->
      <section class="landing-how py-12 py-md-16 bg-surface">
        <v-container>
          <h2 class="text-h4 font-weight-bold text-center mb-10">Get Onboarded in 3 Simple Steps</h2>
          <v-row justify="center">
            <v-col v-for="(step, i) in steps" :key="i" cols="12" sm="4" class="text-center">
              <v-avatar color="primary" size="56" class="mb-4">
                <span class="text-h5 font-weight-bold text-white">{{ i + 1 }}</span>
              </v-avatar>
              <h3 class="text-subtitle-1 font-weight-semibold mb-1">{{ step.title }}</h3>
              <p class="text-body-2 text-medium-emphasis">{{ step.desc }}</p>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── Contact / CTA Section ───────────────────────────────────── -->
      <section class="landing-cta py-12 py-md-16">
        <v-container>
          <v-card
            flat
            rounded="xl"
            class="pa-8 pa-md-12 text-center cta-card"
            color="primary"
          >
            <h2 class="text-h4 font-weight-bold text-white mb-3">Ready to Digitise Your Centre?</h2>
            <p class="text-body-1 text-white mb-8" style="opacity: 0.9; max-width: 550px; margin: 0 auto;">
              Reach out and we'll help you get set up. It's quick, personal, and free to start.
            </p>

            <v-row justify="center" class="ga-4">
              <v-col cols="12" sm="auto">
                <v-btn
                  size="x-large"
                  rounded="lg"
                  color="white"
                  class="text-none font-weight-semibold text-primary"
                  href="https://wa.me/919944926396?text=Hi%2C%20I%20want%20to%20onboard%20my%20matrimonial%20centre%20on%20Varanbook"
                  target="_blank"
                  rel="noopener"
                  block
                >
                  <v-icon start color="green">mdi-whatsapp</v-icon>
                  WhatsApp: +91 99449 26396
                </v-btn>
              </v-col>
              <v-col cols="12" sm="auto">
                <v-btn
                  size="x-large"
                  rounded="lg"
                  variant="outlined"
                  color="white"
                  class="text-none font-weight-semibold"
                  href="mailto:support@varanbook.in?subject=Onboarding%20Request"
                  block
                >
                  <v-icon start>mdi-email-outline</v-icon>
                  support@varanbook.in
                </v-btn>
              </v-col>
            </v-row>
          </v-card>
        </v-container>
      </section>

      <!-- ── Footer ──────────────────────────────────────────────────── -->
      <footer class="py-6 text-center">
        <p class="text-caption text-medium-emphasis mb-1">
          © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
        </p>
        <router-link
          to="/privacy-policy"
          class="text-caption text-medium-emphasis text-decoration-none"
          style="opacity: 0.8;"
        >Privacy Policy</router-link>
      </footer>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
const features = [
  {
    icon: 'mdi-account-multiple-plus',
    color: 'primary',
    title: 'Profile Management',
    desc: 'Create and manage detailed matrimonial profiles with photos, bio-data, and partner preferences — all digital, all searchable.',
  },
  {
    icon: 'mdi-heart-multiple',
    color: 'accent',
    title: 'Smart Shortlisting',
    desc: 'Shortlist compatible matches for families in a click. Share curated recommendations they will love.',
  },
  {
    icon: 'mdi-card-account-details',
    color: 'secondary',
    title: 'Membership Plans',
    desc: 'Define flexible membership tiers with validity tracking. Manage renewals and payments with ease.',
  },
  {
    icon: 'mdi-account-group',
    color: 'success',
    title: 'Multi-tenant Ready',
    desc: 'Run multiple centres or branches under one roof. Each tenant gets its own isolated data space.',
  },
  {
    icon: 'mdi-shield-lock',
    color: 'error',
    title: 'Secure & Private',
    desc: 'Role-based access control, encrypted data, and privacy-first design keep sensitive family data safe.',
  },
  {
    icon: 'mdi-cellphone-check',
    color: 'primary',
    title: 'Mobile Friendly',
    desc: 'Works beautifully on phones, tablets, and desktops — so you and families can access profiles anywhere.',
  },
]

const steps = [
  {
    title: 'Contact Us',
    desc: 'Send us a WhatsApp message or email. Tell us about your centre and requirements.',
  },
  {
    title: 'We Set You Up',
    desc: 'We create your tenant space, configure plans, and onboard your team — usually within 24 hours.',
  },
  {
    title: 'Start Managing',
    desc: 'Log in, add profiles, match families, and grow your centre with a powerful digital platform.',
  },
]
</script>

<style scoped>
.landing-brand {
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.02em;
}

.landing-hero {
  padding: 4rem 0 3rem;
}

.landing-headline {
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 700;
  line-height: 1.15;
  font-family: 'Inter', system-ui, sans-serif;
}

.landing-subtext {
  font-size: clamp(1rem, 2.5vw, 1.2rem);
  line-height: 1.7;
  max-width: 540px;
}

@media (max-width: 959px) {
  .landing-subtext {
    margin-left: auto;
    margin-right: auto;
  }
}

.landing-hero-icon {
  opacity: 0.15;
}

.feature-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid rgba(30, 136, 229, 0.08);
}
.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(30, 136, 229, 0.12);
}

.cta-card {
  background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%) !important;
}
</style>
