<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api } from '@/services/api'
import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
import type { DataSourceMode } from '@/types'

const festivalStore = useFestivalStore()
const settingsStore = useSettingsStore()
const sourceSwitchPending = ref(false)
const sourceSwitchError = ref<string | null>(null)
const sourceSwitchSummary = ref<string | null>(null)

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

function normalizeVenueScore(value: number | null | undefined): -1 | 0 | 1 {
  if ((value ?? 0) > 0) return 1
  if ((value ?? 0) < 0) return -1
  return 0
}

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

const currentSourceDescription = computed(() =>
  settingsStore.dataSourceMode === 'prod'
    ? 'Live (prod) : utilise le programme courant quand il est disponible.'
    : 'Démo (archive) : utile avant le dévoilement complet du programme.',
)

async function switchDataSource(mode: DataSourceMode) {
  if (sourceSwitchPending.value || settingsStore.dataSourceMode === mode) {
    return
  }

  sourceSwitchPending.value = true
  sourceSwitchError.value = null
  sourceSwitchSummary.value = null

  try {
    settingsStore.setDataSourceMode(mode)
    const summary = await api.importCatalog(2025, mode)
    await festivalStore.bootstrap()
    sourceSwitchSummary.value = [
      `${summary.films_created + summary.films_updated} film(s) traités`,
      `${summary.screenings_created + summary.screenings_updated} séance(s) traitée(s)`,
      summary.warnings_count > 0 ? `${summary.warnings_count} warning(s)` : null,
    ]
      .filter(Boolean)
      .join(' · ')
  } catch {
    sourceSwitchError.value =
      mode === 'prod'
        ? 'Impossible de charger la source live pour le moment.'
        : 'Impossible de recharger la source démo archive pour le moment.'
  } finally {
    sourceSwitchPending.value = false
  }
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
          <h3>Source de données</h3>
          <p class="page-copy">Réglage technique secondaire. La source démo s'appuie sur l'archive ; la source live sert le programme courant dès qu'il est disponible.</p>
        </div>
      </header>

      <p class="settings__status">{{ currentSourceDescription }}</p>

      <div class="settings__choice-group settings__choice-group--start" role="radiogroup" aria-label="Source de données">
        <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': settingsStore.dataSourceMode === 'demo' }" :disabled="sourceSwitchPending" @click="switchDataSource('demo')">
          <span class="settings__choice-mark" aria-hidden="true">D</span>
          <span>Démo (archive)</span>
        </button>
        <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': settingsStore.dataSourceMode === 'prod' }" :disabled="sourceSwitchPending" @click="switchDataSource('prod')">
          <span class="settings__choice-mark" aria-hidden="true">L</span>
          <span>Live (prod)</span>
        </button>
      </div>

      <p v-if="sourceSwitchPending" class="settings__status">Import en cours puis rechargement du catalogue…</p>
      <p v-else-if="sourceSwitchSummary" class="settings__status">{{ sourceSwitchSummary }}</p>
      <p v-if="sourceSwitchError" class="settings__status settings__status--error">{{ sourceSwitchError }}</p>
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
          <div v-for="venue in knownVenues" :key="venue" class="settings__venue-row">
            <span>{{ venue }}</span>
            <div class="settings__choice-group" role="radiogroup" :aria-label="`Confort pour ${venue}`">
              <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': normalizeVenueScore(settingsStore.recommendationSettings.preferredVenueScores[venue]) === 0 }" @click="settingsStore.setVenueScore(venue, null)">
                <span class="settings__choice-mark" aria-hidden="true">0</span>
                <span>Sans avis</span>
              </button>
              <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': normalizeVenueScore(settingsStore.recommendationSettings.preferredVenueScores[venue]) === 1 }" @click="settingsStore.setVenueScore(venue, 1)">
                <span class="settings__choice-mark" aria-hidden="true">+</span>
                <span>Bien</span>
              </button>
              <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': normalizeVenueScore(settingsStore.recommendationSettings.preferredVenueScores[venue]) === -1 }" @click="settingsStore.setVenueScore(venue, -1)">
                <span class="settings__choice-mark" aria-hidden="true">-</span>
                <span>Pas confo</span>
              </button>
            </div>
          </div>
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
