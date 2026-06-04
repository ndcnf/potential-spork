<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'

const festivalStore = useFestivalStore()
const settingsStore = useSettingsStore()

onMounted(() => {
  settingsStore.load()
  if (!festivalStore.cycles.length && !festivalStore.loading) {
    festivalStore.bootstrap()
  }
})

const knownVenues = computed(() => {
  const names = festivalStore.visibleScreenings.map((screening) => screening.venue_name).filter(Boolean) as string[]
  return [...new Set(names)].sort((left, right) => left.localeCompare(right))
})

function formatMinutesForInput(minutes: number | null | undefined): string {
  if (minutes == null) return ''
  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return `${String(hours).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

function parseInputTime(value: string): number | null {
  if (!value) return null
  const [hours, minutes] = value.split(':').map(Number)
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null
  return hours * 60 + minutes
}

function updateAvoidWindow(beforeValue: string, afterValue: string) {
  settingsStore.setAvoidBeforeMinutes(parseInputTime(beforeValue))
  settingsStore.setAvoidAfterMinutes(parseInputTime(afterValue))
}
</script>

<template>
  <section class="page settings">
    <header class="page-header">
      <div>
        <h2>Parametres</h2>
        <p class="page-copy">
          Zone secondaire du produit. Ces reglages influencent seulement les recommandations du planning et ne remplacent pas vos choix.
        </p>
      </div>
    </header>

    <section class="settings__panel">
      <header class="settings__section-header">
        <div>
          <h3>Recommandations du planning</h3>
          <p class="page-copy">Activez ou non l'aide a la decision dans le planning.</p>
        </div>
        <label class="settings__switch" :class="{ 'settings__switch--active': settingsStore.recommendationSettings.enabled }">
          <input
            type="checkbox"
            :checked="settingsStore.recommendationSettings.enabled"
            @change="settingsStore.setRecommendationEnabled(($event.target as HTMLInputElement).checked)"
          />
          <span class="settings__switch-ui" aria-hidden="true"><span class="settings__switch-knob" /></span>
          <span>{{ settingsStore.recommendationSettings.enabled ? 'Activees' : 'Desactivees' }}</span>
        </label>
      </header>

      <p class="settings__status">
        <template v-if="settingsStore.recommendationMode === 'off'">Recommandations desactivees : le planning reste entierement manuel.</template>
        <template v-else-if="settingsStore.recommendationMode === 'neutral'">Recommandations actives, mais sans preference definie : l'app reste neutre.</template>
        <template v-else>Recommandations actives avec preferences personnalisees.</template>
      </p>
    </section>

    <section class="settings__panel" :class="{ 'settings__panel--inactive': !settingsStore.recommendationSettings.enabled }">
      <header class="settings__section-header">
        <div>
          <h3>Confort des salles</h3>
          <p class="page-copy">Vous pouvez favoriser ou penaliser certaines salles. Laissez vide pour rester neutre.</p>
        </div>
      </header>

      <fieldset class="settings__fieldset" :disabled="!settingsStore.recommendationSettings.enabled">
        <div class="settings__venues">
          <label v-for="venue in knownVenues" :key="venue" class="settings__venue-row">
            <span>{{ venue }}</span>
            <select
              :value="settingsStore.recommendationSettings.preferredVenueScores[venue] ?? ''"
              @change="settingsStore.setVenueScore(venue, ($event.target as HTMLSelectElement).value === '' ? null : Number(($event.target as HTMLSelectElement).value))"
            >
              <option value="">Neutre</option>
              <option :value="2">Tres favorable</option>
              <option :value="1">Plutot favorable</option>
              <option :value="0">Neutre</option>
              <option :value="-1">Plutot a eviter</option>
              <option :value="-2">A eviter</option>
            </select>
          </label>
        </div>
      </fieldset>
    </section>

    <section class="settings__panel" :class="{ 'settings__panel--inactive': !settingsStore.recommendationSettings.enabled }">
      <header class="settings__section-header">
        <div>
          <h3>Preferences horaires</h3>
          <p class="page-copy">Optionnel. Ce sont des preferences souples pour orienter les recommandations, pas des interdictions strictes.</p>
        </div>
      </header>

      <fieldset class="settings__fieldset" :disabled="!settingsStore.recommendationSettings.enabled">
        <div class="settings__time-window">
          <label>
            <span>Je prefere eviter les seances avant</span>
            <input
              type="time"
              :value="formatMinutesForInput(settingsStore.recommendationSettings.avoidBeforeMinutes)"
              @change="updateAvoidWindow(($event.target as HTMLInputElement).value, formatMinutesForInput(settingsStore.recommendationSettings.avoidAfterMinutes))"
            />
          </label>

          <label>
            <span>Je prefere eviter les seances apres</span>
            <input
              type="time"
              :value="formatMinutesForInput(settingsStore.recommendationSettings.avoidAfterMinutes)"
              @change="updateAvoidWindow(formatMinutesForInput(settingsStore.recommendationSettings.avoidBeforeMinutes), ($event.target as HTMLInputElement).value)"
            />
          </label>
        </div>
      </fieldset>
    </section>

    <section class="settings__panel settings__panel--danger">
      <button type="button" class="ghost-button" @click="settingsStore.resetRecommendationSettings()">Reinitialiser les recommandations</button>
    </section>
  </section>
</template>
