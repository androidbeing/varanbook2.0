<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center" style="min-height: 80vh">
      <v-col cols="12" class="text-center">
        <v-icon color="primary" size="96">mdi-heart-broken</v-icon>
        <h1 class="text-h2 font-weight-bold text-primary mt-4">404</h1>
        <p class="text-h6 text-medium-emphasis mb-8">
          Oops! The page you're looking for doesn't exist.
        </p>
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-home"
          @click="router.push('/')"
        >
          Go Home
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
