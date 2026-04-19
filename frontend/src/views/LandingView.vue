<template>
  <v-app>
    <!-- ── Top App Bar ─────────────────────────────────────────────────── -->
    <v-app-bar flat class="px-2 px-sm-4 landing-navbar" elevation="0">
      <v-app-bar-title>
        <div class="d-flex align-center ga-2">
          <v-icon color="primary" size="28">mdi-heart-circle</v-icon>
          <span class="text-h5 font-weight-bold landing-brand">Varanbook</span>
        </div>
      </v-app-bar-title>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        rounded="pill"
        size="default"
        class="text-none font-weight-semibold px-5"
        :to="{ name: 'login' }"
      >
        <v-icon start size="18">mdi-login</v-icon>
        Login
      </v-btn>
    </v-app-bar>

    <v-main>
      <!-- ── Hero Section ────────────────────────────────────────────── -->
      <section class="landing-hero">
        <!-- Decorative blobs -->
        <div class="blob blob-1" />
        <div class="blob blob-2" />
        <div class="blob blob-3" />

        <v-container class="hero-container">
          <v-row align="center" justify="center">
            <!-- Left: Copy -->
            <v-col cols="12" md="6" class="text-center text-md-start hero-text-col">
              <v-chip
                color="primary"
                variant="tonal"
                size="small"
                rounded="pill"
                class="mb-5 font-weight-medium"
              >
                <v-icon start size="14">mdi-star-four-points</v-icon>
                Purpose-built for Matrimonial Centres
              </v-chip>

              <h1 class="landing-headline mb-5">
                Manage Your<br />
                Matrimonial Centre —<br />
                <span class="gradient-text">Effortlessly</span>
              </h1>

              <p class="landing-subtext text-medium-emphasis mb-8">
                Varanbook is a modern platform built exclusively for
                <strong>matrimonial information centres</strong>. Digitise profiles, manage
                memberships, share shortlists, and delight families — all from one place.
              </p>

              <div class="d-flex flex-column flex-sm-row ga-3 justify-center justify-md-start mb-8">
                <v-btn
                  color="primary"
                  size="x-large"
                  rounded="pill"
                  class="text-none font-weight-semibold px-7 hero-cta-primary"
                  href="https://wa.me/919944926396?text=Hi%2C%20I%20want%20to%20onboard%20my%20matrimonial%20centre%20on%20Varanbook"
                  target="_blank"
                  rel="noopener"
                  elevation="3"
                >
                  <v-icon start>mdi-whatsapp</v-icon>
                  Get Started on WhatsApp
                </v-btn>
                <v-btn
                  variant="outlined"
                  color="primary"
                  size="x-large"
                  rounded="pill"
                  class="text-none font-weight-medium px-6"
                  :to="{ name: 'login' }"
                >
                  Already onboarded? Login
                </v-btn>
              </div>

              <!-- Trust badges -->
              <div class="d-flex flex-wrap ga-4 justify-center justify-md-start trust-badges">
                <div v-for="badge in trustBadges" :key="badge.label" class="d-flex align-center ga-2">
                  <v-icon :color="badge.color" size="18">{{ badge.icon }}</v-icon>
                  <span class="text-caption text-medium-emphasis font-weight-medium">{{ badge.label }}</span>
                </div>
              </div>
            </v-col>

            <!-- Right: Hero visual -->
            <v-col cols="12" md="6" class="d-none d-md-flex justify-center align-center">
              <div class="hero-visual">
                <!-- Main card -->
                <v-card rounded="xl" class="hero-main-card pa-5" elevation="12">
                  <div class="d-flex align-center ga-3 mb-5">
                    <v-avatar color="primary" size="44">
                      <v-icon color="white" size="24">mdi-account-heart</v-icon>
                    </v-avatar>
                    <div>
                      <div class="text-subtitle-2 font-weight-bold">Meena Profiles</div>
                      <div class="text-caption text-medium-emphasis">Premium Centre</div>
                    </div>
                    <v-spacer />
                    <v-chip color="success" size="x-small" variant="tonal">Active</v-chip>
                  </div>

                  <v-row class="mb-4" dense>
                    <v-col v-for="stat in heroStats" :key="stat.label" cols="4">
                      <div class="hero-stat-box rounded-lg pa-3 text-center">
                        <div class="text-h6 font-weight-bold text-primary">{{ stat.value }}</div>
                        <div class="text-caption text-medium-emphasis">{{ stat.label }}</div>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Profile list preview -->
                  <div v-for="profile in heroProfiles" :key="profile.name" class="d-flex align-center ga-3 py-2 hero-profile-row">
                    <v-avatar :color="profile.color" size="36">
                      <v-icon color="white" size="18">mdi-account</v-icon>
                    </v-avatar>
                    <div class="flex-grow-1">
                      <div class="text-body-2 font-weight-medium">{{ profile.name }}</div>
                      <div class="text-caption text-medium-emphasis">{{ profile.detail }}</div>
                    </div>
                    <v-icon size="16" color="primary">mdi-heart-outline</v-icon>
                  </div>
                </v-card>

                <!-- Floating badge: match -->
                <div class="hero-badge hero-badge-match floating-slow">
                  <v-icon color="success" size="16">mdi-check-circle</v-icon>
                  <span class="text-caption font-weight-semibold">New Match Found!</span>
                </div>

                <!-- Floating badge: shortlist -->
                <div class="hero-badge hero-badge-shortlist floating-fast">
                  <v-icon color="primary" size="16">mdi-star</v-icon>
                  <span class="text-caption font-weight-semibold">3 Shortlisted</span>
                </div>
              </div>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── Stats Bar ───────────────────────────────────────────────── -->
      <section class="stats-bar">
        <v-container>
          <v-row justify="center">
            <v-col v-for="s in stats" :key="s.label" cols="6" sm="3" class="text-center">
              <div class="stats-number text-primary">{{ s.value }}</div>
              <div class="text-caption text-medium-emphasis font-weight-medium">{{ s.label }}</div>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── Features Section ────────────────────────────────────────── -->
      <section class="landing-features py-14 py-md-20">
        <v-container>
          <div class="section-label text-center mb-2">
            <v-chip color="secondary" variant="tonal" size="small" rounded="pill">
              <v-icon start size="14">mdi-lightning-bolt</v-icon>
              Features
            </v-chip>
          </div>
          <h2 class="text-h4 font-weight-bold text-center mb-3">Why Centres Love Varanbook</h2>
          <p class="text-body-1 text-medium-emphasis text-center mb-12 section-subtitle">
            Purpose-built tools that save time, impress families, and grow your business.
          </p>

          <v-row justify="center">
            <v-col v-for="feature in features" :key="feature.title" cols="12" sm="6" md="4">
              <v-card flat rounded="xl" class="pa-6 feature-card fill-height">
                <div class="feature-icon-wrap mb-5" :class="`icon-bg-${feature.colorKey}`">
                  <v-icon :color="feature.color" size="28">{{ feature.icon }}</v-icon>
                </div>
                <h3 class="text-h6 font-weight-bold mb-2">{{ feature.title }}</h3>
                <p class="text-body-2 text-medium-emphasis">{{ feature.desc }}</p>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── How It Works ────────────────────────────────────────────── -->
      <section class="landing-how py-14 py-md-20">
        <v-container>
          <div class="text-center mb-2">
            <v-chip color="primary" variant="tonal" size="small" rounded="pill">
              <v-icon start size="14">mdi-map-marker-path</v-icon>
              How It Works
            </v-chip>
          </div>
          <h2 class="text-h4 font-weight-bold text-center mb-12">Get Onboarded in 3 Simple Steps</h2>
          <v-row justify="center" align="start">
            <v-col v-for="(step, i) in steps" :key="i" cols="12" sm="4" class="text-center step-col">
              <!-- Connector line (between steps on desktop) -->
              <div v-if="i < steps.length - 1" class="step-connector d-none d-sm-block" />

              <div class="step-number-wrap mx-auto mb-5">
                <div class="step-number">{{ i + 1 }}</div>
              </div>
              <v-icon :color="step.color" size="36" class="mb-4">{{ step.icon }}</v-icon>
              <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ step.title }}</h3>
              <p class="text-body-2 text-medium-emphasis">{{ step.desc }}</p>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── Testimonial / Social Proof ─────────────────────────────── -->
      <section class="landing-testimonial py-14 py-md-20">
        <v-container>
          <v-row justify="center">
            <v-col cols="12" md="8" class="text-center">
              <v-icon color="primary" size="40" class="mb-4">mdi-format-quote-open</v-icon>
              <p class="testimonial-text text-h6 font-weight-regular mb-6">
                "Varanbook transformed how we run our centre. We went from paper registers to a fully
                digital system in a single day. Families love how professional our shortlists look now."
              </p>
              <v-avatar color="primary" size="52" class="mb-3">
                <v-icon color="white" size="28">mdi-account</v-icon>
              </v-avatar>
              <div class="text-subtitle-2 font-weight-bold">Lakshmi Priya</div>
              <div class="text-caption text-medium-emphasis">Owner, Sri Lakshmi Matrimonial Centre</div>
              <div class="d-flex justify-center ga-1 mt-2">
                <v-icon v-for="n in 5" :key="n" color="amber" size="18">mdi-star</v-icon>
              </div>
            </v-col>
          </v-row>
        </v-container>
      </section>

      <!-- ── CTA Section ────────────────────────────────────────────── -->
      <section class="landing-cta py-12 py-md-16">
        <v-container>
          <div class="cta-card rounded-xl pa-8 pa-md-14 text-center">
            <v-chip color="white" variant="tonal" size="small" rounded="pill" class="mb-5">
              <v-icon start size="14">mdi-rocket-launch</v-icon>
              Free to Start
            </v-chip>
            <h2 class="text-h4 font-weight-bold text-white mb-3">Ready to Digitise Your Centre?</h2>
            <p class="text-body-1 mb-8 cta-subtitle">
              Reach out and we'll help you get set up. It's quick, personal, and free to start.
            </p>

            <div class="d-flex flex-column flex-sm-row ga-4 justify-center">
              <v-btn
                size="x-large"
                rounded="pill"
                color="white"
                class="text-none font-weight-semibold text-primary px-8"
                href="https://wa.me/919944926396?text=Hi%2C%20I%20want%20to%20onboard%20my%20matrimonial%20centre%20on%20Varanbook"
                target="_blank"
                rel="noopener"
                elevation="4"
              >
                <v-icon start color="green-darken-1">mdi-whatsapp</v-icon>
                +91 99449 26396
              </v-btn>
              <v-btn
                size="x-large"
                rounded="pill"
                variant="outlined"
                color="white"
                class="text-none font-weight-medium px-8"
                href="mailto:support@varanbook.in?subject=Onboarding%20Request"
              >
                <v-icon start>mdi-email-outline</v-icon>
                support@varanbook.in
              </v-btn>
            </div>
          </div>
        </v-container>
      </section>

      <!-- ── Footer ──────────────────────────────────────────────────── -->
      <footer class="py-8 text-center landing-footer">
        <div class="d-flex align-center justify-center ga-2 mb-3">
          <v-icon color="primary" size="20">mdi-heart-circle</v-icon>
          <span class="text-body-2 font-weight-bold landing-brand">Varanbook</span>
        </div>
        <p class="text-caption text-medium-emphasis mb-2">
          © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
        </p>
        <router-link
          to="/privacy-policy"
          class="text-caption text-medium-emphasis text-decoration-none"
          style="opacity: 0.7;"
        >Privacy Policy</router-link>
      </footer>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
const trustBadges = [
  { icon: 'mdi-shield-check', color: 'success', label: 'Secure & Private' },
  { icon: 'mdi-cellphone-check', color: 'primary', label: 'Mobile Friendly' },
  { icon: 'mdi-clock-fast', color: 'orange', label: 'Setup in 24 hrs' },
]

const heroStats = [
  { value: '248', label: 'Profiles' },
  { value: '34', label: 'Matches' },
  { value: '12', label: 'Shortlists' },
]

const heroProfiles = [
  { name: 'Ananya R.', detail: '26 yrs · Software Engineer', color: 'pink-darken-1' },
  { name: 'Karthik S.', detail: '29 yrs · Doctor', color: 'indigo' },
  { name: 'Divya M.', detail: '24 yrs · Teacher', color: 'teal' },
]

const stats = [
  { value: '500+', label: 'Profiles Managed' },
  { value: '50+', label: 'Centres Onboarded' },
  { value: '1000+', label: 'Families Served' },
  { value: '24 hrs', label: 'Avg. Setup Time' },
]

const features = [
  {
    icon: 'mdi-account-multiple-plus',
    color: 'primary',
    colorKey: 'primary',
    title: 'Profile Management',
    desc: 'Create and manage detailed matrimonial profiles with photos, bio-data, and partner preferences — all digital, all searchable.',
  },
  {
    icon: 'mdi-heart-multiple',
    color: 'pink',
    colorKey: 'pink',
    title: 'Smart Shortlisting',
    desc: 'Shortlist compatible matches for families in a click. Share curated recommendations they will love.',
  },
  {
    icon: 'mdi-card-account-details',
    color: 'purple',
    colorKey: 'purple',
    title: 'Membership Plans',
    desc: 'Define flexible membership tiers with validity tracking. Manage renewals and payments with ease.',
  },
  {
    icon: 'mdi-star-crescent',
    color: 'teal',
    colorKey: 'teal',
    title: 'Built-In Horoscope',
    desc: 'Powered by Astrosidda.in — generate and match horoscopes directly within the platform, so families get accurate Jathagam support in one place.',
  },
  {
    icon: 'mdi-shield-lock',
    color: 'red',
    colorKey: 'red',
    title: 'Secure & Private',
    desc: 'Role-based access control, encrypted data, and privacy-first design keep sensitive family data safe.',
  },
  {
    icon: 'mdi-cellphone-check',
    color: 'orange',
    colorKey: 'orange',
    title: 'Mobile Friendly',
    desc: 'Works beautifully on phones, tablets, and desktops — so you and families can access profiles anywhere.',
  },
]

const steps = [
  {
    icon: 'mdi-whatsapp',
    color: 'success',
    title: 'Contact Us',
    desc: 'Send us a WhatsApp message or email. Tell us about your centre and requirements.',
  },
  {
    icon: 'mdi-cog-play',
    color: 'primary',
    title: 'We Set You Up',
    desc: 'We create your tenant space, configure plans, and onboard your team — usually within 24 hours.',
  },
  {
    icon: 'mdi-rocket-launch',
    color: 'pink',
    title: 'Start Managing',
    desc: 'Log in, add profiles, match families, and grow your centre with a powerful digital platform.',
  },
]
</script>

<style scoped>
/* ── Brand / Navbar ──────────────────────────────────────────────── */
.landing-brand {
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #1E88E5, #7B1FA2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.landing-navbar {
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.85) !important;
  border-bottom: 1px solid rgba(30, 136, 229, 0.08);
}

/* ── Hero ────────────────────────────────────────────────────────── */
.landing-hero {
  position: relative;
  overflow: hidden;
  padding: 5rem 0 3rem;
  background: linear-gradient(160deg, #f0f7ff 0%, #fdf0ff 50%, #fff8f0 100%);
}

.hero-container {
  position: relative;
  z-index: 1;
}

.hero-text-col {
  position: relative;
  z-index: 1;
}

/* Decorative blobs */
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  pointer-events: none;
}
.blob-1 {
  width: 480px; height: 480px;
  background: radial-gradient(circle, #90CAF9, #1E88E5);
  top: -120px; left: -140px;
}
.blob-2 {
  width: 380px; height: 380px;
  background: radial-gradient(circle, #CE93D8, #7B1FA2);
  top: 60px; right: -100px;
}
.blob-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #FFCC80, #F57C00);
  bottom: -80px; left: 40%;
}

.landing-headline {
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 800;
  line-height: 1.15;
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.03em;
  color: #1a1a2e;
}

.gradient-text {
  background: linear-gradient(135deg, #1E88E5, #7B1FA2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.landing-subtext {
  font-size: clamp(1rem, 2.5vw, 1.15rem);
  line-height: 1.75;
  max-width: 520px;
}

@media (max-width: 959px) {
  .landing-subtext { margin-left: auto; margin-right: auto; }
  .trust-badges { justify-content: center; }
}

.hero-cta-primary {
  box-shadow: 0 8px 24px rgba(30, 136, 229, 0.35) !important;
  transition: box-shadow 0.2s, transform 0.2s;
}
.hero-cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(30, 136, 229, 0.45) !important;
}

/* ── Hero Visual ─────────────────────────────────────────────────── */
.hero-visual {
  position: relative;
  width: 380px;
  max-width: 100%;
}

.hero-main-card {
  background: rgba(255, 255, 255, 0.92) !important;
  backdrop-filter: blur(16px);
  border: 1px solid rgba(30, 136, 229, 0.12);
}

.hero-stat-box {
  background: linear-gradient(135deg, #f0f7ff, #fdf0ff);
  border: 1px solid rgba(30, 136, 229, 0.1);
}

.hero-profile-row {
  border-top: 1px solid rgba(0,0,0,0.05);
}

.hero-badge {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  border-radius: 999px;
  padding: 8px 14px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  white-space: nowrap;
  font-size: 0.78rem;
}

.hero-badge-match {
  bottom: -16px;
  left: -20px;
}

.hero-badge-shortlist {
  top: 20px;
  right: -24px;
}

/* ── Floating animations ─────────────────────────────────────────── */
@keyframes float-slow {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}
@keyframes float-fast {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
}
.floating-slow { animation: float-slow 4s ease-in-out infinite; }
.floating-fast { animation: float-fast 3s ease-in-out infinite 0.5s; }

/* ── Stats Bar ───────────────────────────────────────────────────── */
.stats-bar {
  padding: 3rem 0;
  background: white;
  border-top: 1px solid rgba(30, 136, 229, 0.08);
  border-bottom: 1px solid rgba(30, 136, 229, 0.08);
}

.stats-number {
  font-size: 2rem;
  font-weight: 800;
  font-family: 'Inter', system-ui, sans-serif;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

/* ── Features ────────────────────────────────────────────────────── */
.landing-features {
  background: linear-gradient(180deg, #f8faff 0%, #fff 100%);
}

.section-subtitle {
  max-width: 580px;
  margin: 0 auto;
}

.feature-card {
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  border: 1px solid rgba(30, 136, 229, 0.08);
  background: white;
}
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(30, 136, 229, 0.14) !important;
}

.feature-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-bg-primary { background: linear-gradient(135deg, #E3F2FD, #BBDEFB); }
.icon-bg-pink    { background: linear-gradient(135deg, #FCE4EC, #F8BBD0); }
.icon-bg-purple  { background: linear-gradient(135deg, #F3E5F5, #E1BEE7); }
.icon-bg-teal    { background: linear-gradient(135deg, #E0F2F1, #B2DFDB); }
.icon-bg-red     { background: linear-gradient(135deg, #FFEBEE, #FFCDD2); }
.icon-bg-orange  { background: linear-gradient(135deg, #FFF3E0, #FFE0B2); }

/* ── How It Works ────────────────────────────────────────────────── */
.landing-how {
  background: linear-gradient(160deg, #fdf0ff 0%, #f0f7ff 100%);
}

.step-col {
  position: relative;
}

.step-connector {
  position: absolute;
  top: 28px;
  right: -50%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #1E88E5, #7B1FA2);
  opacity: 0.2;
  z-index: 0;
}

.step-number-wrap {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1E88E5, #7B1FA2);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 20px rgba(30, 136, 229, 0.3);
  position: relative;
  z-index: 1;
}

.step-number {
  font-size: 1.4rem;
  font-weight: 800;
  color: white;
  font-family: 'Inter', system-ui, sans-serif;
}

/* ── Testimonial ─────────────────────────────────────────────────── */
.landing-testimonial {
  background: white;
}

.testimonial-text {
  line-height: 1.8;
  color: #444;
  font-style: italic;
}

/* ── CTA ─────────────────────────────────────────────────────────── */
.cta-card {
  background: linear-gradient(135deg, #1565C0 0%, #6A1B9A 60%, #E65100 120%) !important;
  position: relative;
  overflow: hidden;
}

.cta-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.cta-subtitle {
  color: rgba(255,255,255,0.85);
  max-width: 520px;
  margin: 0 auto;
}

/* ── Footer ──────────────────────────────────────────────────────── */
.landing-footer {
  background: #fafafa;
  border-top: 1px solid rgba(0,0,0,0.06);
}
</style>
