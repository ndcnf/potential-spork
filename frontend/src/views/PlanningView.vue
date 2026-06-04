<script setup lang="ts">
import { computed, reactive } from 'vue'
import { RouterLink } from 'vue-router'

import { useIcalExport } from '@/composables/useIcalExport'
import { usePlanningModel } from '@/composables/usePlanningModel'

const { exportHref, exportIcal, exportScreeningIcal } = useIcalExport()

const {
  store,
  settingsStore,
  activeDay,
  planningMode,
  screeningFilter,
  effectivePlanningMode,
  dayOptions,
  dayScreenings,
  timelineGroups,
  detailScreening,
  relatedFilmScreenings,
  conflictingSelectedScreenings,
  arbitrableScreenings,
  summary,
  daySummary,
  visualizationGroups,
  formatDayLabel,
  formatTimeRange,
  filmPriorityDots,
  filmMeta,
  screeningReason,
  screeningStatusTone,
  screeningComparisonStatus,
  screeningStateClass,
  screeningComparisonHints,
  screeningDecisionNote,
  screeningPrimaryActionLabel,
  visualizationBlockClass,
  selectedCountForDay,
  dayChipLabel,
  setScreeningSelection,
  clearScreeningSelection,
  openDetailPanel,
  focusFirstConflict,
  focusFirstArbitration,
  closeDetailPanel,
  FESTIVAL_VIEW_KEY,
  isMobile,
} = usePlanningModel()

const transitionFeedback = reactive<{ message: string; tone: 'info' | 'success'; visible: boolean; timer: ReturnType<typeof setTimeout> | null }>({
  message: '',
  tone: 'info',
  visible: false,
  timer: null,
})

const hasPlanningCandidates = computed(() => summary.value.films > 0)
const hasConflicts = computed(() => summary.value.conflicts > 0)
const hasArbitrations = computed(() => summary.value.toPlace > 0)
const initialLoading = computed(() => store.loading && !store.screenings.length && !store.cycles.length)

const planningGuidance = computed(() => {
  if (!hasPlanningCandidates.value) {
    return {
      title: 'Commence par qualifier quelques films',
      copy: "Tu n'as pas encore assez de films qualifiés pour arbitrer ton planning.",
      actionLabel: 'Retourner à Films',
      actionTo: '/films',
    }
  }

  if (!hasConflicts.value && !hasArbitrations.value) {
    return {
      title: 'Planning presque complet',
      copy: "Aucun conflit pour l'instant. Ton planning est lisible sur cette plage.",
      actionLabel: 'Revoir la sélection de films',
      actionTo: '/films',
    }
  }

  if (hasConflicts.value) {
    return {
      title: 'Arbitrage requis',
      copy: 'Commence par résoudre les collisions entre séances déjà retenues avant d’ajouter de nouveaux choix.',
      actionLabel: null,
      actionTo: null,
    }
  }

  return {
    title: 'Choisis la meilleure séance par film',
    copy: 'Tu peux maintenant confirmer ou remplacer les séances restantes sans surcharger le planning.',
    actionLabel: null,
    actionTo: null,
  }
})

function showTransitionFeedback(message: string, tone: 'info' | 'success' = 'success') {
  if (transitionFeedback.timer) {
    clearTimeout(transitionFeedback.timer)
  }

  transitionFeedback.message = message
  transitionFeedback.tone = tone
  transitionFeedback.visible = true
  transitionFeedback.timer = setTimeout(() => {
    transitionFeedback.visible = false
    transitionFeedback.timer = null
  }, 2600)
}

async function applyScreeningSelection(screeningId: number, nextStatus: 'tentative' | 'confirmed' | 'rejected') {
  const screening = dayScreenings.value.find((item) => item.id === screeningId) ?? relatedFilmScreenings.value.find((item) => item.id === screeningId)

  await setScreeningSelection(screeningId, nextStatus)

  if (!screening) {
    return
  }

  if (nextStatus === 'confirmed') {
    showTransitionFeedback(`Séance confirmée pour ${screening.film_title}.`)
    return
  }

  if (nextStatus === 'rejected') {
    showTransitionFeedback(`Séance ignorée pour ${screening.film_title}.`, 'info')
    return
  }

  if (screening.selection_status === 'none' && (screening.isAlternative || screening.derived_state === 'disabled')) {
    showTransitionFeedback(`Cette séance remplace ton autre choix pour ${screening.film_title}.`)
    return
  }

  showTransitionFeedback(`Séance ajoutée au planning pour ${screening.film_title}.`)
}

async function removeScreeningSelection(screeningId: number) {
  const screening = dayScreenings.value.find((item) => item.id === screeningId) ?? relatedFilmScreenings.value.find((item) => item.id === screeningId)

  await clearScreeningSelection(screeningId)

  if (screening) {
    showTransitionFeedback(`Séance retirée du planning pour ${screening.film_title}.`, 'info')
  }
}
</script>

<template>
  <section class="page planning">
    <section v-if="initialLoading" class="page planning" aria-label="Chargement du planning">
      <header class="page-header skeleton-block">
        <div>
          <span class="skeleton-line skeleton-line--xs" />
          <span class="skeleton-line skeleton-line--md" />
          <span class="skeleton-line skeleton-line--lg" />
        </div>
        <span class="skeleton-button" />
      </header>

      <section class="planning__guidance skeleton-block">
        <div>
          <span class="skeleton-line skeleton-line--xs" />
          <span class="skeleton-line skeleton-line--md" />
          <span class="skeleton-line skeleton-line--lg" />
        </div>
        <span class="skeleton-button" />
      </section>

      <section class="planning__meta-panel skeleton-block">
        <div class="planning__summary">
          <span class="skeleton-card" />
          <span class="skeleton-card" />
          <span class="skeleton-card" />
          <span class="skeleton-card" />
        </div>
      </section>

      <section class="planning__panel planning__panel--day skeleton-block">
        <span class="skeleton-line skeleton-line--md" />
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
        <p class="eyebrow">Étape 2 sur 2</p>
        <h2>Planning</h2>
        <p class="page-copy">Arbitre les collisions et retiens la bonne séance pour chaque film déjà qualifié.</p>
      </div>
      <a class="planning__export" :href="exportHref" target="_blank" rel="noopener" @click="exportIcal">Exporter iCal</a>
    </header>

    <section v-if="store.loadError" class="notice-panel notice-panel--warning">
      <h3>API indisponible</h3>
      <p class="page-copy">{{ store.loadError }}</p>
    </section>

    <section class="planning__guidance">
      <div>
        <p class="eyebrow">Action principale</p>
        <h3>{{ planningGuidance.title }}</h3>
        <p class="page-copy">{{ planningGuidance.copy }}</p>
      </div>

      <div class="planning__guidance-actions">
        <button v-if="hasConflicts" type="button" class="planning__action planning__action--primary" @click="focusFirstConflict">
          Voir le premier conflit
        </button>
        <button v-else-if="hasArbitrations" type="button" class="planning__action planning__action--primary" @click="focusFirstArbitration">
          Voir la première séance à arbitrer
        </button>
        <RouterLink v-else-if="planningGuidance.actionLabel && planningGuidance.actionTo" :to="planningGuidance.actionTo" class="planning__action planning__action--secondary">
          {{ planningGuidance.actionLabel }}
        </RouterLink>
      </div>
    </section>

    <section
      v-if="transitionFeedback.visible"
      class="notice-panel notice-panel--toast"
      :class="transitionFeedback.tone === 'success' ? 'notice-panel--success' : 'notice-panel--info'"
    >
      <p class="page-copy">{{ transitionFeedback.message }}</p>
    </section>

    <section class="planning__meta-panel">
      <div class="planning__summary">
        <article class="planning__summary-card">
          <strong>{{ summary.films }}</strong>
          <span>films retenus</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.selected }}</strong>
          <span>séances choisies</span>
        </article>
        <button type="button" class="planning__summary-card planning__summary-card--action" :disabled="!conflictingSelectedScreenings.length" @click="focusFirstConflict">
          <strong>{{ summary.conflicts }}</strong>
          <span>conflits à régler</span>
        </button>
        <button type="button" class="planning__summary-card planning__summary-card--action" :disabled="!arbitrableScreenings.length" @click="focusFirstArbitration">
          <strong>{{ summary.toPlace }}</strong>
          <span>séances à arbitrer</span>
        </button>
      </div>

      <section class="legend legend--planning">
        <div class="legend__group">
          <span class="legend__label">États</span>
          <div class="legend__items legend__items--compact">
            <span class="legend__item"><span class="legend__marker legend__marker--confirmed" /> confirmée</span>
            <span class="legend__item"><span class="legend__marker legend__marker--tentative" /> tentative</span>
            <span class="legend__item"><span class="legend__marker legend__marker--must-lock" /> à sécuriser</span>
            <span class="legend__item"><span class="legend__marker legend__marker--conflict" /> conflit</span>
            <span class="legend__item"><span class="legend__marker legend__marker--disabled" /> autre séance déjà choisie</span>
            <span class="legend__item"><span class="legend__marker legend__marker--rejected" /> séance écartée</span>
            <span class="legend__item"><span class="legend__marker legend__marker--available" /> disponible</span>
          </div>
        </div>
      </section>

      <section class="planning__controls-panel">
        <div class="planning__control-group planning__control-group--status">
          <p class="eyebrow">Recommandations</p>
          <p class="planning__status-note">
            <template v-if="settingsStore.recommendationMode === 'off'">Désactivées. L'arbitrage reste entièrement manuel.</template>
            <template v-else-if="settingsStore.recommendationMode === 'neutral'">Activées, mais sans préférence définie : l'app reste neutre.</template>
            <template v-else>Activées et personnalisées selon tes préférences.</template>
          </p>
        </div>

        <div class="planning__control-group">
          <p class="eyebrow">Jour</p>
          <div class="planning__day-picker">
            <button
              v-for="day in dayOptions"
              :key="day"
              class="planning__day-button"
              :class="{ 'planning__day-button--active': activeDay === day }"
              type="button"
              @click="activeDay = day"
            >
              {{ dayChipLabel(day) }} · {{ selectedCountForDay(day) }}
            </button>
          </div>
        </div>

        <div class="planning__control-group">
          <p class="eyebrow">Affichage</p>
          <div class="planning__mode-switch" role="tablist" aria-label="Affichage planning">
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'timeline' }" type="button" @click="planningMode = 'timeline'">
              Timeline
            </button>
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'visualization' }" type="button" @click="planningMode = 'visualization'">
              Visualisation
            </button>
          </div>
          <p v-if="isMobile && planningMode === 'visualization'" class="planning__status-note">Visualisation simplifiée indisponible sur mobile : affichage automatique en timeline.</p>
        </div>

        <div class="planning__control-group">
          <p class="eyebrow">Filtre</p>
          <div class="planning__mode-switch" role="tablist" aria-label="Filtre des séances">
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': screeningFilter === 'all' }" type="button" @click="screeningFilter = 'all'">
              Toutes
            </button>
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': screeningFilter === 'confirmed' }" type="button" @click="screeningFilter = 'confirmed'">
              Confirmées uniquement
            </button>
          </div>
        </div>
      </section>
    </section>

      <section v-if="hasPlanningCandidates" class="planning__focus-layout" :class="{ 'planning__focus-layout--with-panel': !!detailScreening }">
      <section class="planning__panel planning__panel--day">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Jour courant</p>
            <h3>{{ activeDay === FESTIVAL_VIEW_KEY ? 'Festival entier' : activeDay ? formatDayLabel(activeDay) : 'Aucun jour' }}</h3>
          </div>
          <span>{{ daySummary.selected }} séances retenues · {{ daySummary.conflicts }} conflit(s) · {{ daySummary.total }} séance(s)</span>
        </header>

        <div v-if="effectivePlanningMode === 'timeline' && dayScreenings.length" class="planning__timeline">
          <template v-for="group in timelineGroups" :key="group.dayKey || 'empty'">
            <header v-if="activeDay === FESTIVAL_VIEW_KEY" class="planning__timeline-day-header">
              <strong>{{ formatDayLabel(group.dayKey) }}</strong>
              <span>{{ group.screenings.filter((screening) => screening.isSelected).length }} séances retenues</span>
            </header>

            <article
              v-for="screening in group.screenings"
              :key="screening.id"
              class="planning__timeline-item"
              :class="screeningStateClass(screening)"
            >
              <div class="planning__timeline-time">{{ formatTimeRange(screening) }}</div>
              <div class="planning__timeline-track">
                <div class="planning__timeline-marker" />
                <div class="planning__timeline-content">
                  <div class="planning__timeline-header">
                    <div class="planning__film-heading">
                      <strong>
                        <button type="button" class="planning__detail-trigger" @click="openDetailPanel(screening.id)">
                          {{ screening.film_title }}
                        </button>
                      </strong>
                      <span v-if="filmPriorityDots(screening.film?.priority)" class="planning__film-priority" aria-hidden="true">
                        <span v-for="dot in filmPriorityDots(screening.film?.priority)" :key="dot" class="planning__film-priority-dot" />
                      </span>
                    </div>
                    <span class="planning__status-pill" :class="`planning__status-pill--${screeningStatusTone(screening)}`">
                      <span class="planning__status-pill-dot" />
                      {{ screeningReason(screening) }}
                    </span>
                  </div>
                  <p>{{ screening.venue_name }}</p>
                  <p>{{ filmMeta(screening) }}</p>
                  <div class="planning__session-links">
                    <a v-if="screening.ticket_url" :href="screening.ticket_url" target="_blank" rel="noopener">billetterie</a>
                    <a href="#" @click="exportScreeningIcal(screening, $event)">agenda</a>
                  </div>
                  <div class="planning__detail-actions" aria-label="Actions sur la séance">
                    <button
                      v-if="screening.selection_status === 'tentative'"
                      type="button"
                      class="planning__action planning__action--primary"
                      @click="applyScreeningSelection(screening.id, 'confirmed')"
                    >
                      Confirmer cette séance
                    </button>
                    <button
                      v-else-if="screening.selection_status !== 'confirmed'"
                      type="button"
                      class="planning__action planning__action--primary"
                      @click="applyScreeningSelection(screening.id, 'tentative')"
                    >
                      {{ screeningPrimaryActionLabel(screening) }}
                    </button>

                    <button
                      v-if="screening.selection_status === 'confirmed'"
                      type="button"
                      class="planning__action planning__action--secondary"
                      @click="applyScreeningSelection(screening.id, 'tentative')"
                    >
                      Repasser en tentative
                    </button>
                    <button
                      v-if="screening.selection_status === 'tentative' || screening.selection_status === 'confirmed'"
                      type="button"
                      class="planning__action planning__action--ghost"
                      @click="removeScreeningSelection(screening.id)"
                    >
                      Retirer du planning
                    </button>
                    <button
                      v-else-if="screening.selection_status !== 'rejected'"
                      type="button"
                      class="planning__action planning__action--ghost"
                      @click="applyScreeningSelection(screening.id, 'rejected')"
                    >
                      Ignorer cette séance
                    </button>
                  </div>
                </div>
              </div>
            </article>
          </template>
        </div>

        <div v-else-if="effectivePlanningMode === 'visualization' && visualizationGroups.length" class="planning__visualization-view">
          <template v-for="group in visualizationGroups" :key="group.dayKey || 'visual-empty'">
            <header v-if="activeDay === FESTIVAL_VIEW_KEY" class="planning__timeline-day-header">
              <strong>{{ formatDayLabel(group.dayKey) }}</strong>
              <span>{{ group.lanes.length }} salle(s)</span>
            </header>

            <div v-if="group.lanes.length" class="planning__visual-grid" :style="{ '--planning-buckets': String(group.bucketCount), '--planning-venues': String(group.lanes.length) }">
              <div class="planning__visual-header">
                <div class="planning__visual-corner" />
                <div class="planning__visual-venue-headers">
                  <div v-for="lane in group.lanes" :key="`${group.dayKey}-${lane.venueName}-header`" class="planning__visual-venue-header">
                    {{ lane.venueName }}
                  </div>
                </div>
              </div>

              <div class="planning__visual-body">
                <div class="planning__visual-scale">
                  <span v-for="(label, index) in group.bucketLabels" :key="`${group.dayKey}-${index}`" class="planning__visual-scale-label">
                    <template v-if="index < group.bucketLabels.length - 1 && index % 4 === 0">{{ label }}</template>
                  </span>
                </div>

                <div class="planning__visual-lanes">
                  <div v-for="lane in group.lanes" :key="`${group.dayKey}-${lane.venueName}`" class="planning__visual-lane">
                    <div class="planning__visual-track">
                      <div
                        v-for="block in lane.blocks"
                        :key="block.id"
                        class="planning__visual-block"
                        :class="visualizationBlockClass(block)"
                        :style="{ gridRow: `${block.visualRowStart} / span ${block.visualRowSpan}` }"
                        :title="`${block.film_title} · ${formatTimeRange(block)}`"
                        @click="openDetailPanel(block.id)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <p v-else class="planning__empty">Aucune séance choisie à visualiser pour cette plage.</p>
          </template>
        </div>

        <p v-else class="planning__empty">Aucune séance visible pour ce jour.</p>
      </section>

      <aside v-if="detailScreening" class="planning__detail-panel">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Détail film</p>
            <h3 class="planning__detail-title">
              <span>{{ detailScreening.film_title }}</span>
              <span v-if="filmPriorityDots(detailScreening.film?.priority)" class="planning__film-priority" aria-hidden="true">
                <span v-for="dot in filmPriorityDots(detailScreening.film?.priority)" :key="dot" class="planning__film-priority-dot" />
              </span>
            </h3>
            <p v-if="detailScreening.film?.premiere_label" class="planning__detail-kicker">{{ detailScreening.film.premiere_label }}</p>
          </div>
          <button type="button" class="planning__action planning__action--ghost" @click="closeDetailPanel">Fermer</button>
        </header>

        <div v-if="detailScreening.film?.short_description" class="planning__detail-copy">
          <p>{{ detailScreening.film.short_description }}</p>
        </div>

        <div class="planning__detail-media" v-if="detailScreening.film?.poster_url">
          <img :src="detailScreening.film.poster_url" :alt="`Affiche ${detailScreening.film_title}`" />
        </div>

        <div class="planning__detail-grid">
          <div>
            <p class="planning__detail-line"><strong>Horaire</strong> {{ formatTimeRange(detailScreening) }}</p>
            <p class="planning__detail-line"><strong>Salle</strong> {{ detailScreening.venue_name || 'Salle inconnue' }}</p>
            <p class="planning__detail-line planning__detail-line--status">
              <strong>Statut</strong>
              <span class="planning__status-pill" :class="`planning__status-pill--${screeningStatusTone(detailScreening)}`">
                <span class="planning__status-pill-dot" />
                {{ screeningReason(detailScreening) }}
              </span>
            </p>
          </div>
          <div>
            <p class="planning__detail-line"><strong>Réalisation</strong> {{ detailScreening.film?.directors || 'Non renseignée' }}</p>
            <p class="planning__detail-line"><strong>Infos</strong> {{ filmMeta(detailScreening) }}</p>
            <p class="planning__detail-line"><strong>Tagline</strong> {{ detailScreening.film?.tagline || 'Non renseignée' }}</p>
            <p class="planning__detail-line"><strong>Langue</strong> {{ detailScreening.film?.language || 'Non renseignée' }}</p>
            <p class="planning__detail-line"><strong>Âge</strong> {{ detailScreening.film?.age_rating || 'Non renseigné' }}</p>
          </div>
        </div>

        <div v-if="relatedFilmScreenings.length" class="planning__detail-copy">
          <p class="planning__detail-copy-title">{{ relatedFilmScreenings.length > 1 ? 'Comparer les séances de ce film' : 'Séance de ce film' }}</p>
          <p class="planning__detail-copy-subtitle">
            {{ relatedFilmScreenings.length > 1 ? 'Commence par choisir ou remplacer une séance, puis ajuste son statut si besoin.' : 'Cette séance peut être retenue telle quelle ou remplacée plus tard.' }}
          </p>
          <div class="planning__detail-screenings">
            <article
              v-for="option in relatedFilmScreenings"
              :key="option.id"
              class="planning__detail-screening"
              :class="screeningStateClass(option)"
            >
              <div class="planning__detail-screening-main">
                <div>
                  <strong>
                    <button type="button" class="planning__detail-trigger" @click="openDetailPanel(option.id)">
                      {{ formatDayLabel(option.dayKey) }} · {{ formatTimeRange(option) }}
                    </button>
                  </strong>
                  <span>{{ option.venue_name }}</span>
                </div>
                <span class="planning__status-pill" :class="`planning__status-pill--${screeningStatusTone(option)}`">
                  <span class="planning__status-pill-dot" />
                  {{ screeningComparisonStatus(option) }}
                </span>
              </div>
              <div v-if="screeningComparisonHints(option).length" class="planning__detail-hints">
                <span v-for="hint in screeningComparisonHints(option)" :key="hint" class="planning__detail-hint">{{ hint }}</span>
              </div>
              <p class="planning__detail-note">{{ screeningDecisionNote(option) }}</p>
              <div class="planning__detail-actions">
                <button
                  v-if="option.selection_status === 'tentative'"
                  type="button"
                  class="planning__action planning__action--primary"
                  @click="applyScreeningSelection(option.id, 'confirmed')"
                >
                  Confirmer cette séance
                </button>
                <button
                  v-else-if="option.selection_status !== 'confirmed'"
                  type="button"
                  class="planning__action planning__action--primary"
                  @click="applyScreeningSelection(option.id, 'tentative')"
                >
                  {{ screeningPrimaryActionLabel(option) }}
                </button>

                <button
                  v-if="option.selection_status === 'confirmed'"
                  type="button"
                  class="planning__action planning__action--secondary"
                  @click="applyScreeningSelection(option.id, 'tentative')"
                >
                  Repasser en tentative
                </button>
                <button
                  v-if="option.selection_status === 'tentative' || option.selection_status === 'confirmed'"
                  type="button"
                  class="planning__action planning__action--ghost"
                  @click="removeScreeningSelection(option.id)"
                >
                  Retirer du planning
                </button>
                <button
                  v-else-if="option.selection_status !== 'rejected'"
                  type="button"
                  class="planning__action planning__action--ghost"
                  @click="applyScreeningSelection(option.id, 'rejected')"
                >
                  Ignorer cette séance
                </button>
              </div>
              <div class="planning__session-links">
                <a v-if="option.ticket_url" :href="option.ticket_url" target="_blank" rel="noopener">billetterie</a>
                <a href="#" @click="exportScreeningIcal(option, $event)">agenda</a>
              </div>
            </article>
          </div>
        </div>

        <div v-if="detailScreening.film?.synopsis" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Synopsis</p>
          <p>{{ detailScreening.film.synopsis }}</p>
        </div>

        <div v-if="detailScreening.film?.cast" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Casting</p>
          <p>{{ detailScreening.film.cast }}</p>
        </div>

        <div class="planning__links">
          <a href="#" @click="exportScreeningIcal(detailScreening, $event)">Ajouter cette séance à l’agenda</a>
          <a v-if="detailScreening.ticket_url" :href="detailScreening.ticket_url" target="_blank" rel="noopener">Billetterie</a>
          <a v-if="detailScreening.film?.festival_url" :href="detailScreening.film.festival_url" target="_blank" rel="noopener">Ouvrir la fiche NIFFF</a>
          <a v-if="detailScreening.film?.imdb_url" :href="detailScreening.film.imdb_url" target="_blank" rel="noopener">IMDb</a>
        </div>
      </aside>
      </section>

      <section v-else class="empty-panel">
        <h3>Aucun film à arbitrer pour le moment</h3>
        <p class="page-copy">Tu dois d'abord marquer au moins un film comme `Immanquable` ou `Peut-être` dans la vue `Films`.</p>
        <RouterLink to="/films" class="ghost-button">Retourner à Films</RouterLink>
      </section>
    </template>
  </section>
</template>
