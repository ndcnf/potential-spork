<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { useFestivalStore } from '@/stores/festival'
import { useSettingsStore } from '@/stores/settings'
import type { DataSourceMode, RecommendationSortCriterion } from '@/types'

const festivalStore = useFestivalStore()
const settingsStore = useSettingsStore()
const draftDataSourceMode = ref<DataSourceMode>('demo')
const recommendationCriterionOptions: Array<{ value: RecommendationSortCriterion; label: string }> = [
  { value: 'options', label: 'Peu d’options restantes' },
  { value: 'score', label: 'Meilleure salle / horaire' },
  { value: 'conflicts', label: 'Moins de conflits' },
]

onMounted(() => {
  settingsStore.load()
  draftDataSourceMode.value = settingsStore.dataSourceMode
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

  signals.push(
    `ordre : ${settingsStore.recommendationSettings.criterionOrder
      .map((criterion) => recommendationCriterionOptions.find((option) => option.value === criterion)?.label.toLowerCase() ?? criterion)
      .join(' · ')}`,
  )

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

function updateRecommendationCriterionOrder(index: number, value: string) {
  if (value === 'options' || value === 'score' || value === 'conflicts') {
    settingsStore.setRecommendationCriterionOrder(index, value)
  }
}

function liveSourceUrlForRequest(): string | undefined {
  const value = settingsStore.liveSourceUrl.trim()
  return value || undefined
}

function liveSourceUrlForDisplay(): string {
  return liveSourceUrlForRequest() ?? 'https://nifff.ch/programme/'
}

const currentSourceDescription = computed(() =>
  draftDataSourceMode.value === 'prod'
    ? 'Source sélectionnée : Live (prod). Renseigne l’URL puis récupère le programme courant.'
    : 'Source sélectionnée : Démo (archive). Lit la DB démo déjà importée depuis Wayback.',
)

const sourceRuntimeDescription = computed(() => festivalStore.sourceStatus.description)

const sourceSwitchSummary = computed(() => {
  const summary = festivalStore.lastImportSummary
  if (!summary) {
    return null
  }

  return [
    `${summary.films_created + summary.films_updated} film(s) traité(s)`,
    `${summary.screenings_created + summary.screenings_updated} séance(s) traitée(s)`,
    summary.warnings_count > 0 ? `${summary.warnings_count} warning(s)` : null,
  ]
    .filter(Boolean)
    .join(' · ')
})

const resetChoicesSummary = computed(() =>
  festivalStore.usingMocks
    ? 'Les choix locaux seront effacés puis la démonstration sera rechargée.'
    : 'Les choix locaux et les sélections de séances seront remis à zéro avant rechargement.',
)

async function switchDataSource(mode: DataSourceMode) {
  if (festivalStore.sourceSwitchPending || (mode === 'demo' && settingsStore.dataSourceMode === mode)) {
    return
  }

  if (
    mode === 'prod' &&
    !window.confirm(`Récupérer les données live depuis ${liveSourceUrlForDisplay()} ? Le catalogue courant sera remplacé par la source live.`)
  ) {
    return
  }

  try {
    await festivalStore.switchSource(mode, mode === 'prod' ? liveSourceUrlForRequest() : undefined)
    settingsStore.setDataSourceMode(mode)
  } catch {
    festivalStore.loadError =
      mode === 'prod'
        ? 'Impossible de charger la source live pour le moment.'
        : 'Impossible de recharger la source démo archive pour le moment.'
  }
}

function selectDataSource(mode: DataSourceMode) {
  if (festivalStore.sourceSwitchPending) {
    return
  }

  draftDataSourceMode.value = mode

  if (mode === 'demo') {
    switchDataSource('demo')
  }
}

async function resetChoices() {
  if (festivalStore.sourceSwitchPending) {
    return
  }

  try {
    await festivalStore.resetUserChoices()
  } catch {
    festivalStore.loadError = 'Impossible de réinitialiser les choix pour le moment.'
  }
}

async function reimportCurrentSource() {
  if (festivalStore.sourceSwitchPending) {
    return
  }

  try {
    await festivalStore.reimportCurrentSource(
      settingsStore.dataSourceMode,
      settingsStore.dataSourceMode === 'prod' ? liveSourceUrlForRequest() : undefined,
    )
  } catch {
    festivalStore.loadError = 'Impossible de relancer un import propre pour le moment.'
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
          <p class="page-copy">Réglage technique secondaire. La source démo lit la DB archive ; le bouton d'import sert seulement à rafraîchir rarement cette DB depuis Wayback.</p>
        </div>
      </header>

      <p class="settings__status">{{ currentSourceDescription }}</p>
      <p class="settings__status">{{ sourceRuntimeDescription }}</p>

      <div class="settings__choice-group settings__choice-group--start" role="radiogroup" aria-label="Source de données">
        <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': draftDataSourceMode === 'demo' }" :disabled="festivalStore.sourceSwitchPending" @click="selectDataSource('demo')">
          <span class="settings__choice-mark" aria-hidden="true">D</span>
          <span>Démo (archive)</span>
        </button>
        <button type="button" class="settings__choice-pill" :class="{ 'settings__choice-pill--active': draftDataSourceMode === 'prod' }" :disabled="festivalStore.sourceSwitchPending" @click="selectDataSource('prod')">
          <span class="settings__choice-mark" aria-hidden="true">L</span>
          <span>Live (prod)</span>
        </button>
      </div>

      <div v-if="draftDataSourceMode === 'prod'" class="settings__source-url">
        <label>
          <span>URL source live</span>
          <input
            type="url"
            :value="settingsStore.liveSourceUrl"
            placeholder="https://nifff.ch/programme/"
            :disabled="festivalStore.sourceSwitchPending"
            @change="settingsStore.setLiveSourceUrl(($event.target as HTMLInputElement).value)"
          />
        </label>
        <button type="button" class="ghost-button" :disabled="festivalStore.sourceSwitchPending" @click="switchDataSource('prod')">
          Récupérer Live
        </button>
      </div>

      <p v-if="festivalStore.sourceSwitchPending" class="settings__status">Import en cours puis rechargement du catalogue…</p>
      <p v-else-if="sourceSwitchSummary" class="settings__status">{{ sourceSwitchSummary }}</p>
      <p v-if="festivalStore.loadError" class="settings__status settings__status--error">{{ festivalStore.loadError }}</p>

      <div v-if="draftDataSourceMode !== 'prod'" class="settings__actions-row">
        <button type="button" class="ghost-button" :disabled="festivalStore.sourceSwitchPending" @click="reimportCurrentSource()">
          Refaire un import propre
        </button>
      </div>
    </section>

    <section class="settings__panel settings__panel--danger">
      <header class="settings__section-header">
        <div>
          <h3>Réinitialiser mes choix</h3>
          <p class="page-copy">Remet les films à `À traiter` côté interface et annule les sélections de séances pour repartir d’un état propre.</p>
        </div>
      </header>

      <p class="settings__status">{{ resetChoicesSummary }}</p>
      <div class="settings__actions-row">
        <button type="button" class="ghost-button" :disabled="festivalStore.sourceSwitchPending" @click="resetChoices()">Reset les choix</button>
      </div>
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
          <span class="settings__impact-pill">films immanquables d’abord</span>
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
          <h3>Ordre d’arbitrage</h3>
          <p class="page-copy">Les films immanquables restent toujours prioritaires. Ces réglages départagent ensuite les séances entre elles.</p>
        </div>
      </header>

      <fieldset class="settings__fieldset" :disabled="!settingsStore.recommendationSettings.enabled">
        <div class="settings__order-list">
          <div class="settings__select-row">
            <span>Priorité fixe</span>
            <strong>Immanquables avant peut-être</strong>
          </div>
          <label
            v-for="(criterion, index) in settingsStore.recommendationSettings.criterionOrder"
            :key="`${criterion}-${index}`"
            class="settings__select-row"
          >
            <span>Critère {{ index + 1 }}</span>
            <select :value="criterion" @change="updateRecommendationCriterionOrder(index, ($event.target as HTMLSelectElement).value)">
              <option v-for="option in recommendationCriterionOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
      </fieldset>
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
