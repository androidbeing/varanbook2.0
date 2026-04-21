<template>
  <v-app>
    <v-main class="bg-background">
      <v-container class="py-10" style="max-width: 860px">
        <!-- Header -->
        <div class="text-center mb-8">
          <h1 class="text-h4 font-weight-bold text-primary">Varanbook</h1>
          <p class="text-body-2 text-medium-emphasis">Privacy Policy</p>
        </div>

        <v-card elevation="2" rounded="xl" class="pa-6 pa-md-10">
          <p class="text-caption text-medium-emphasis mb-6">
            <strong>Last updated:</strong> March 2026
          </p>

          <!-- Section 1 -->
          <h2 class="text-h6 font-weight-bold mb-2">1. Introduction</h2>
          <p class="text-body-2 mb-6">
            Varanbook ("we", "our", or "us") is a matrimonial matchmaking platform that helps
            families and individuals connect for the purpose of marriage. We are committed to
            protecting your personal information and your right to privacy. This Privacy Policy
            describes how we collect, use, disclose, and safeguard your information when you use
            our platform. Please read this policy carefully. If you disagree with its terms,
            please discontinue use of the platform.
          </p>

          <!-- Section 2 -->
          <h2 class="text-h6 font-weight-bold mb-2">2. Information We Collect</h2>
          <p class="text-body-2 mb-3">
            When you create or manage a profile on Varanbook, we may collect the following
            categories of personal information:
          </p>
          <v-list density="compact" class="mb-4 pa-0">
            <v-list-item
              v-for="item in dataCollected"
              :key="item.label"
              :prepend-icon="item.icon"
              :title="item.label"
              :subtitle="item.detail"
              class="px-0 mb-1"
            />
          </v-list>
          <p class="text-body-2 mb-6">
            We collect this information directly from you, from tenant administrators managing
            your account, and automatically through your use of the platform.
          </p>

          <!-- Section 3 -->
          <h2 class="text-h6 font-weight-bold mb-2">3. How We Use Your Information</h2>
          <p class="text-body-2 mb-3">We use your personal information to:</p>
          <ul class="text-body-2 mb-6 pl-6">
            <li class="mb-1">Create and manage your matrimonial profile</li>
            <li class="mb-1">Suggest and display compatible profiles to other members within your organization or community (tenant)</li>
            <li class="mb-1">Facilitate the shortlisting and communication process between families</li>
            <li class="mb-1">Send email notifications for password resets and important account communications</li>
            <li class="mb-1">Allow tenant administrators to onboard and manage members</li>
            <li class="mb-1">Maintain platform security through audit logs and activity monitoring</li>
            <li class="mb-1">Comply with applicable legal obligations</li>
          </ul>

          <!-- Section 4 -->
          <h2 class="text-h6 font-weight-bold mb-2">4. Sharing of Your Information</h2>
          <p class="text-body-2 mb-3">
            Your personal information is shared only within the boundaries described below:
          </p>
          <ul class="text-body-2 mb-6 pl-6">
            <li class="mb-1">
              <strong>Within your tenant (organization/community):</strong> Your profile details are visible to other verified members and administrators of the same tenant who are using Varanbook for matchmaking purposes.
            </li>
            <li class="mb-1">
              <strong>Super administrators:</strong> Platform-level administrators may access account data for support, compliance, and operational purposes.
            </li>
            <li class="mb-1">
              <strong>Service providers:</strong> We use trusted third-party services (such as AWS for hosting, S3 for file storage, and an email delivery service) that process data on our behalf under strict data protection agreements.
            </li>
            <li class="mb-1">
              <strong>Legal requirements:</strong> We may disclose your data if required by law, court order, or governmental authority.
            </li>
          </ul>
          <p class="text-body-2 mb-6">
            We do <strong>not</strong> sell, trade, or rent your personal information to third parties for marketing purposes.
          </p>

          <!-- Section 5 -->
          <h2 class="text-h6 font-weight-bold mb-2">5. Profile Photos and Horoscope Documents</h2>
          <p class="text-body-2 mb-6">
            Photos and horoscope documents you upload are stored securely in encrypted cloud storage
            (AWS S3). Access to these files is controlled and they are accessible only to members
            within your tenant. You may request removal of your files at any time by contacting
            your tenant administrator or reaching out to us directly.
          </p>

          <!-- Section 6 -->
          <h2 class="text-h6 font-weight-bold mb-2">6. Data Retention</h2>
          <p class="text-body-2 mb-6">
            We retain your personal information for as long as your account remains active or as
            needed to provide services. If you request account deletion, we will delete or
            anonymize your personal data within 30 days, except where we are legally required to
            retain it (e.g., audit logs for compliance purposes, which are retained for up to
            12 months).
          </p>

          <!-- Section 7 -->
          <h2 class="text-h6 font-weight-bold mb-2">7. Data Security</h2>
          <p class="text-body-2 mb-6">
            We implement industry-standard security measures to protect your personal data,
            including:
          </p>
          <ul class="text-body-2 mb-6 pl-6">
            <li class="mb-1">Passwords are stored as secure cryptographic hashes (never in plain text)</li>
            <li class="mb-1">All data in transit is encrypted using TLS 1.2 or higher</li>
            <li class="mb-1">Data at rest is encrypted using AES-256 encryption</li>
            <li class="mb-1">Access is controlled through role-based authentication (Super Admin, Admin, Member)</li>
            <li class="mb-1">Row-level security (RLS) ensures data isolation between tenants</li>
            <li class="mb-1">Audit logs are maintained for access and modification events</li>
            <li class="mb-1">Password reset tokens are single-use and expire after 1 hour</li>
          </ul>
          <p class="text-body-2 mb-6">
            While we strive to use commercially acceptable means to protect your information, no
            method of transmission over the internet or electronic storage is 100% secure. We
            cannot guarantee absolute security.
          </p>

          <!-- Section 8 -->
          <h2 class="text-h6 font-weight-bold mb-2">8. Your Rights</h2>
          <p class="text-body-2 mb-3">Depending on your location, you may have the following rights:</p>
          <ul class="text-body-2 mb-6 pl-6">
            <li class="mb-1"><strong>Access:</strong> Request a copy of the personal data we hold about you</li>
            <li class="mb-1"><strong>Correction:</strong> Request correction of inaccurate or incomplete data</li>
            <li class="mb-1"><strong>Deletion:</strong> Request deletion of your personal data (subject to legal obligations)</li>
            <li class="mb-1"><strong>Objection:</strong> Object to certain types of processing</li>
            <li class="mb-1"><strong>Portability:</strong> Request transfer of your data in a structured, machine-readable format</li>
          </ul>
          <p class="text-body-2 mb-6">
            To exercise any of these rights, please contact your tenant administrator or reach out
            to us using the contact details in Section 11.
          </p>

          <!-- Section 9 -->
          <h2 class="text-h6 font-weight-bold mb-2">9. Cookies and Tracking</h2>
          <p class="text-body-2 mb-6">
            Varanbook uses minimal browser storage (localStorage) to maintain your authenticated
            session and user preferences. We do not use third-party advertising cookies or
            cross-site tracking technologies. Session tokens are managed securely and expire upon
            logout.
          </p>

          <!-- Section 10 -->
          <h2 class="text-h6 font-weight-bold mb-2">10. Children's Privacy</h2>
          <p class="text-body-2 mb-6">
            Varanbook is intended for adults of marriageable age. We do not knowingly collect
            personal information from individuals under 18 years of age. If we become aware that
            we have collected data from a minor, we will take immediate steps to delete such
            information.
          </p>

          <!-- Section 11 -->
          <h2 class="text-h6 font-weight-bold mb-2">11. Contact Us</h2>
          <p class="text-body-2 mb-2">
            If you have questions, concerns, or requests regarding this Privacy Policy or your
            personal data, please contact us:
          </p>
          <v-card variant="tonal" color="primary" rounded="lg" class="pa-4 mb-6">
            <p class="text-body-2 mb-1"><strong>Varanbook Support</strong></p>
            <p class="text-body-2 mb-1">Email: <a href="mailto:support@varanbook.in" class="text-primary">support@varanbook.in</a></p>
          </v-card>

          <!-- Section 12 -->
          <h2 class="text-h6 font-weight-bold mb-2">12. Changes to This Policy</h2>
          <p class="text-body-2 mb-6">
            We may update this Privacy Policy from time to time to reflect changes in our
            practices or for legal, operational, or regulatory reasons. We will post the updated
            policy on this page with a revised "Last updated" date. Continued use of the platform
            after any changes constitutes your acceptance of the updated policy.
          </p>

          <v-divider class="mb-6" />

          <div class="text-center">
            <v-btn
              variant="text"
              color="primary"
              prepend-icon="mdi-arrow-left"
              @click="$router.back()"
            >
              Back
            </v-btn>
          </div>
        </v-card>

        <p class="text-center text-caption text-medium-emphasis mt-6">
          © {{ new Date().getFullYear() }} Varanbook. All rights reserved.
        </p>
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { useHead } from '@unhead/vue'

useHead({
  title: 'Privacy Policy — Varanbook',
  meta: [
    { name: 'description', content: 'Read the Varanbook Privacy Policy to understand how we collect, use, and protect your personal information.' },
    { property: 'og:title', content: 'Privacy Policy — Varanbook' },
    { property: 'og:url', content: 'https://varanbook.in/privacy-policy' },
    { name: 'robots', content: 'index, follow' },
  ],
  link: [
    { rel: 'canonical', href: 'https://varanbook.in/privacy-policy' },
  ],
})

const dataCollected = [
  {
    icon: 'mdi-account-outline',
    label: 'Identity information',
    detail: 'Full name, date of birth, gender, religion, caste, sub-caste, mother tongue',
  },
  {
    icon: 'mdi-school-outline',
    label: 'Education & career',
    detail: 'Educational qualifications, occupation, employer, annual income',
  },
  {
    icon: 'mdi-map-marker-outline',
    label: 'Location information',
    detail: 'City, state, and country of residence',
  },
  {
    icon: 'mdi-heart-outline',
    label: 'Relationship details',
    detail: 'Marital status, number of children (if any), family background',
  },
  {
    icon: 'mdi-human-male-height',
    label: 'Physical attributes',
    detail: 'Height, complexion, body type, disabilities (optional)',
  },
  {
    icon: 'mdi-star-crescent',
    label: 'Astrological information',
    detail: 'Nakshatra, rashi, gothra, horoscope document (optional)',
  },
  {
    icon: 'mdi-image-outline',
    label: 'Profile photo',
    detail: 'Photographs uploaded for your matrimonial profile',
  },
  {
    icon: 'mdi-account-heart-outline',
    label: 'Partner preferences',
    detail: 'Preferred age range, height, religion, caste, education, and location of prospective match',
  },
  {
    icon: 'mdi-email-outline',
    label: 'Contact information',
    detail: 'Email address used for account login and communication',
  },
]
</script>
