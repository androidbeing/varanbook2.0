<template>
  <v-app>
    <!-- ── Top App Bar ─────────────────────────────────────────────────────── -->
    <v-app-bar color="primary" elevation="2">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title>
        <span class="font-weight-bold text-white">Varanbook</span>
      </v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="toggleTheme">
        <v-icon>{{ isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
      <v-menu>
        <template #activator="{ props }">
          <v-btn icon v-bind="props">
            <v-avatar color="secondary" size="34">
              <span class="text-caption font-weight-bold">
                {{ userInitials }}
              </span>
            </v-avatar>
          </v-btn>
        </template>
        <v-list density="compact" min-width="180">
          <v-list-item :subtitle="auth.user?.email ?? ''" :title="auth.user?.full_name ?? 'User'" />
          <v-divider />
          <v-list-item
            v-if="!auth.isSuperAdmin"
            prepend-icon="mdi-account"
            title="My Profile"
            @click="router.push('/my-profile')"
          />
          <v-list-item
            prepend-icon="mdi-logout"
            title="Sign Out"
            @click="handleLogout"
          />
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- ── Navigation Drawer ──────────────────────────────────────────────── -->
    <v-navigation-drawer v-model="drawer" :temporary="isMobile" color="surface">
      <v-list density="compact" nav>
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          active-color="primary"
          rounded="lg"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- ── Main Content ───────────────────────────────────────────────────── -->
    <v-main>
      <v-container fluid class="pa-4 pa-md-6">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay, useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const { mobile: isMobile } = useDisplay()
const theme = useTheme()

const drawer = ref(!isMobile.value)
const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'varanTheme' : 'varanThemeDark'
}

const userInitials = computed(() => {
  const name = auth.user?.full_name ?? ''
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
})

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

const navItems = computed(() => {
  if (auth.isSuperAdmin) {
    return [
      { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
      { title: 'Tenants', icon: 'mdi-office-building-cog', to: '/admin/tenants' },
    ]
  }
  if (auth.isAdmin) {
    return [
      { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
      { title: 'Browse Profiles', icon: 'mdi-account-group', to: '/profiles' },
    ]
  }
  // Member
  return [
    { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
    { title: 'Browse Profiles', icon: 'mdi-account-group', to: '/profiles' },
    { title: 'My Profile', icon: 'mdi-account-circle', to: '/my-profile' },
  ]
})
</script>
