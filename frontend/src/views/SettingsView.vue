<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

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

const activeRecommendationSignals = computed(() => {
  const signals: string[] = []

  if (Object.keys(settingsStore.recommendationSettings.preferredVenueScores).length > 0) {
    signals.push('salles pondérées')
  }

  if (settingsStore.recommendationSettings.avoidBeforeMinutes !== null) {
    signals.push(`éviter avant ${formatMinutesForInput(settingsStore.recommendationSettings.avoidBeforeMinutes)}`)
  }

  if (settingsStore.recommendationSettings.avoidAfterMinutes !== null) {
    signals.push(`éviter après ${formatMinutesForInput(settingsStore.recommendationSettings.avoidAfterMinutes)}`)
  }

  return signals
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
    <section v-if="festivalStore.loading && !festivalStore.cycles.length" class="page settings" aria-label="Chargement des paramètres">
      <header class="page-header skeleton-block">
        <div>
          <span class="skeleton-line skeleton-line--md" />
          <span class="skeleton-line skeleton-line--lg" />
        </div>
      </header>

      <section class="settings__panel skeleton-block">
        <span class="skeleton-line skeleton-line--sm" />
        <span class="skeleton-field skeleton-field--wide" />
      </section>

      <section class="settings__panel skeleton-block">
        <span class="skeleton-line skeleton-line--sm" />
        <div class="skeleton-list">
          <span class="skeleton-card" />
          <span class="skeleton-card" />
          <span class="skeleton-card" />
        </div>
      </section>
    </section>

    <template v-else>
    <header class="page-header">
      <div>
        <h2>Paramètres</h2>
        <p class="page-copy">
          Zone secondaire du produit. Ces réglages influencent seulement les recommandations du planning et ne remplacent pas tes choix.
        </p>
      </div>
    </header>

    <section v-if="festivalStore.loadError" class="notice-panel notice-panel--warning">
      <h3>Mode démo</h3>
      <p class="page-copy">{{ festivalStore.loadError }}</p>
    </section>

    <section class="settings__panel">
      <header class="settings__section-header">
        <div>
          <h3>Recommandations du planning</h3>
          <p class="page-copy">Active ou non l'aide à la décision dans le planning. Les séances recommandées sont ensuite expliquées directement dans `Planning`.</p>
        </div>
        <label class="settings__switch" :class="{ 'settings__switch--active': settingsStore.recommendationSettings.enabled }">
          <input
            type="checkbox"
            :checked="settingsStore.recommendationSettings.enabled"
            @change="settingsStore.setRecommendationEnabled(($event.target as HTMLInputElement).checked)"
          />
          <span class="settings__switch-ui" aria-hidden="true"><span class="settings__switch-knob" /></span>
          <span>{{ settingsStore.recommendationSettings.enabled ? 'Activées' : 'Désactivées' }}</span>
        </label>
      </header>

      <p class="settings__status">
        <template v-if="settingsStore.recommendationMode === 'off'">Recommandations désactivées : le planning reste entièrement manuel.</template>
        <template v-else-if="settingsStore.recommendationMode === 'neutral'">Recommandations activées, mais sans préférence définie : l'app reste neutre.</template>
        <template v-else>Recommandations activées avec préférences personnalisées.</template>
      </p>

      <div class="settings__impact">
        <p class="settings__impact-title">Ce qui peut faire remonter une séance</p>
        <div class="settings__impact-list">
          <span class="settings__impact-pill">moins de conflits avec le planning</span>
          <span class="settings__impact-pill">peu d’options restantes pour un film</span>
          <span class="settings__impact-pill">salle mieux notée</span>
          <span class="settings__impact-pill">horaire plus compatible</span>
        </div>
        <p v-if="activeRecommendationSignals.length" class="settings__status">Préférences actives : {{ activeRecommendationSignals.join(' · ') }}</p>
        <RouterLink to="/planning" class="ghost-button settings__impact-link">Voir le rendu dans Planning</RouterLink>
      </div>
    </section>

    <section class="settings__panel" :class="{ 'settings__panel--inactive': !settingsStore.recommendationSettings.enabled }">
      <header class="settings__section-header">
        <div>
          <h3>Confort des salles</h3>
          <p class="page-copy">Tu peux favoriser ou pénaliser certaines salles. Ce signal sert seulement à départager les séances quand plusieurs options restent possibles.</p>
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
              <option :value="2">Très favorable</option>
              <option :value="1">Plutôt favorable</option>
              <option :value="0">Neutre</option>
              <option :value="-1">Plutôt à éviter</option>
              <option :value="-2">À éviter</option>
            </select>
          </label>
        </div>
      </fieldset>
    </section>

    <section class="settings__panel" :class="{ 'settings__panel--inactive': !settingsStore.recommendationSettings.enabled }">
      <header class="settings__section-header">
        <div>
          <h3>Préférences horaires</h3>
          <p class="page-copy">Optionnel. Ce sont des préférences souples pour orienter les recommandations, pas des interdictions strictes.</p>
        </div>
      </header>

      <fieldset class="settings__fieldset" :disabled="!settingsStore.recommendationSettings.enabled">
        <div class="settings__time-window">
          <label>
            <span>Éviter si possible les séances avant</span>
            <input
              type="time"
              :value="formatMinutesForInput(settingsStore.recommendationSettings.avoidBeforeMinutes)"
              @change="updateAvoidWindow(($event.target as HTMLInputElement).value, formatMinutesForInput(settingsStore.recommendationSettings.avoidAfterMinutes))"
            />
          </label>

          <label>
            <span>Éviter si possible les séances après</span>
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
      <button type="button" class="ghost-button" @click="settingsStore.resetRecommendationSettings()">Réinitialiser les recommandations</button>
    </section>
    </template>
  </section>
</template>
