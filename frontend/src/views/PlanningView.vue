<script setup lang="ts">
import { usePlanningModel } from '@/composables/usePlanningModel'

const {
  settingsStore,
  activeDay,
  planningMode,
  effectivePlanningMode,
  dayOptions,
  dayScreenings,
  timelineGroups,
  detailScreening,
  relatedFilmScreenings,
  summary,
  daySummary,
  venueGroups,
  visualizationGroups,
  formatDayLabel,
  formatTimeRange,
  filmMeta,
  screeningReason,
  screeningStateClass,
  visualizationBlockClass,
  selectedCountForDay,
  dayChipLabel,
  toggleScreeningSelection,
  openDetailPanel,
  closeDetailPanel,
  exportUrl,
  FESTIVAL_VIEW_KEY,
  isMobile,
} = usePlanningModel()
</script>

<template>
  <section class="page planning">
    <header class="page-header">
      <div>
        <h2>Planning</h2>
        <p class="page-copy">Visualiser le programme dans le temps pour choisir la meilleure seance film par film.</p>
      </div>
      <a class="planning__export" :href="exportUrl" target="_blank" rel="noopener">Exporter iCal</a>
    </header>

    <section class="planning__meta-panel">
      <div class="planning__summary">
        <article class="planning__summary-card">
          <strong>{{ summary.films }}</strong>
          <span>films retenus</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.selected }}</strong>
          <span>seances choisies</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.conflicts }}</strong>
          <span>conflits reels</span>
        </article>
        <article class="planning__summary-card">
          <strong>{{ summary.toPlace }}</strong>
          <span>seances a arbitrer</span>
        </article>
      </div>

      <section class="legend legend--planning">
        <div class="legend__group">
          <span class="legend__label">Etats</span>
          <div class="legend__items legend__items--compact">
            <span class="legend__item"><span class="legend__marker legend__marker--confirmed" /> confirmee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--tentative" /> tentative</span>
            <span class="legend__item"><span class="legend__marker legend__marker--must-lock" /> a securiser</span>
            <span class="legend__item"><span class="legend__marker legend__marker--recommended" /> recommandee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--conflict" /> conflit</span>
            <span class="legend__item"><span class="legend__marker legend__marker--disabled" /> autre seance deja choisie</span>
            <span class="legend__item"><span class="legend__marker legend__marker--rejected" /> seance ecartee</span>
            <span class="legend__item"><span class="legend__marker legend__marker--available" /> disponible</span>
          </div>
        </div>
      </section>

      <section class="planning__controls-panel">
        <div class="planning__control-group planning__control-group--status">
          <p class="eyebrow">Recommandations</p>
          <p class="planning__status-note">
            <template v-if="settingsStore.recommendationMode === 'off'">Desactivees. Le planning reste manuel.</template>
            <template v-else-if="settingsStore.recommendationMode === 'neutral'">Actives, mais sans preference definie : l'app reste neutre.</template>
            <template v-else>Personnalisees selon tes parametres.</template>
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
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'venues' }" type="button" @click="planningMode = 'venues'">
              Par salle
            </button>
            <button class="planning__mode-button" :class="{ 'planning__mode-button--active': planningMode === 'visualization' }" type="button" @click="planningMode = 'visualization'">
              Visualisation
            </button>
          </div>
          <p v-if="isMobile && planningMode === 'visualization'" class="planning__status-note">Visualisation simplifiee indisponible sur mobile : affichage automatique en timeline.</p>
        </div>
      </section>
    </section>

    <section class="planning__focus-layout" :class="{ 'planning__focus-layout--with-panel': !!detailScreening }">
      <section class="planning__panel planning__panel--day">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Jour courant</p>
            <h3>{{ activeDay === FESTIVAL_VIEW_KEY ? 'Festival entier' : activeDay ? formatDayLabel(activeDay) : 'Aucun jour' }}</h3>
          </div>
          <span>{{ daySummary.selected }} choisi(es) · {{ daySummary.conflicts }} conflit(s) · {{ daySummary.total }} seance(s)</span>
        </header>

        <div v-if="effectivePlanningMode === 'timeline' && dayScreenings.length" class="planning__timeline">
          <template v-for="group in timelineGroups" :key="group.dayKey || 'empty'">
            <header v-if="activeDay === FESTIVAL_VIEW_KEY" class="planning__timeline-day-header">
              <strong>{{ formatDayLabel(group.dayKey) }}</strong>
              <span>{{ group.screenings.filter((screening) => screening.isSelected).length }} retenue(s)</span>
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
                    <strong>
                      <button type="button" class="planning__detail-trigger" @click="openDetailPanel(screening.id)">
                        {{ screening.film_title }}
                      </button>
                    </strong>
                    <span class="planning__state">{{ screeningReason(screening) }}</span>
                  </div>
                  <p>{{ screening.venue_name }}</p>
                  <p>{{ filmMeta(screening) }}</p>
                  <div class="planning__selection-toggle" role="radiogroup" aria-label="Statut de la seance">
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'tentative' }"
                      :aria-pressed="screening.selection_status === 'tentative'"
                      @click="toggleScreeningSelection(screening.id, 'tentative')"
                    >
                      Tentative
                    </button>
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'confirmed' }"
                      :aria-pressed="screening.selection_status === 'confirmed'"
                      @click="toggleScreeningSelection(screening.id, 'confirmed')"
                    >
                      Confirmee
                    </button>
                    <button
                      type="button"
                      class="planning__selection-option"
                      :class="{ 'planning__selection-option--active': screening.selection_status === 'rejected' }"
                      :aria-pressed="screening.selection_status === 'rejected'"
                      @click="toggleScreeningSelection(screening.id, 'rejected')"
                    >
                      Ignoree
                    </button>
                  </div>
                </div>
              </div>
            </article>
          </template>
        </div>

        <div v-else-if="effectivePlanningMode === 'venues' && venueGroups.length" class="planning__venues-view">
          <template v-for="group in venueGroups" :key="group.dayKey || 'venues-empty'">
            <header v-if="activeDay === FESTIVAL_VIEW_KEY" class="planning__timeline-day-header">
              <strong>{{ formatDayLabel(group.dayKey) }}</strong>
              <span>{{ group.venues.length }} salle(s)</span>
            </header>

            <div class="planning__matrix">
              <div class="planning__matrix-head">Salle</div>
              <div class="planning__matrix-head">Programme</div>

              <template v-for="row in group.venues" :key="`${group.dayKey}-${row.venueName}`">
                <div class="planning__matrix-venue">{{ row.venueName }}</div>
                <div class="planning__matrix-cell">
                  <article
                    v-for="screening in row.screenings"
                    :key="screening.id"
                    class="planning__matrix-item"
                    :class="screeningStateClass(screening)"
                  >
                    <div class="planning__matrix-time">{{ formatTimeRange(screening) }}</div>
                    <strong>
                      <button type="button" class="planning__detail-trigger" @click="openDetailPanel(screening.id)">
                        {{ screening.film_title }}
                      </button>
                    </strong>
                    <p v-if="screening.isMustLock" class="planning__matrix-note">A securiser</p>
                    <p>{{ screening.film?.tagline || 'Genre non renseigne' }}</p>
                  </article>
                </div>
              </template>
            </div>
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

            <p v-else class="planning__empty">Aucune seance choisie a visualiser pour cette plage.</p>
          </template>
        </div>

        <p v-else class="planning__empty">Aucune seance visible pour ce jour.</p>
      </section>

      <aside v-if="detailScreening" class="planning__detail-panel">
        <header class="planning__panel-header">
          <div>
            <p class="eyebrow">Detail film</p>
            <h3>{{ detailScreening.film_title }}</h3>
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
            <p class="planning__detail-line"><strong>Etat</strong> {{ screeningReason(detailScreening) }}</p>
          </div>
          <div>
            <p class="planning__detail-line"><strong>Rea</strong> {{ detailScreening.film?.directors || 'Non renseigne' }}</p>
            <p class="planning__detail-line"><strong>Infos</strong> {{ filmMeta(detailScreening) }}</p>
            <p class="planning__detail-line"><strong>Genre</strong> {{ detailScreening.film?.tagline || 'Non renseigne' }}</p>
            <p class="planning__detail-line"><strong>Langue</strong> {{ detailScreening.film?.language || 'Non renseignee' }}</p>
            <p class="planning__detail-line"><strong>Age</strong> {{ detailScreening.film?.age_rating || 'Non renseigne' }}</p>
          </div>
        </div>

        <div v-if="relatedFilmScreenings.length > 1" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Comparer les seances de ce film</p>
          <div class="planning__detail-screenings">
            <article
              v-for="option in relatedFilmScreenings"
              :key="option.id"
              class="planning__detail-screening"
              :class="screeningStateClass(option)"
            >
              <div class="planning__detail-screening-main">
                <strong>{{ formatTimeRange(option) }}</strong>
                <span>{{ option.venue_name }}</span>
              </div>
              <p class="planning__detail-screening-note">{{ screeningReason(option) }}</p>
              <div class="planning__selection-toggle" role="radiogroup" aria-label="Statut de la seance du film">
                <button
                  type="button"
                  class="planning__selection-option"
                  :class="{ 'planning__selection-option--active': option.selection_status === 'tentative' }"
                  :aria-pressed="option.selection_status === 'tentative'"
                  @click="toggleScreeningSelection(option.id, 'tentative')"
                >
                  Tentative
                </button>
                <button
                  type="button"
                  class="planning__selection-option"
                  :class="{ 'planning__selection-option--active': option.selection_status === 'confirmed' }"
                  :aria-pressed="option.selection_status === 'confirmed'"
                  @click="toggleScreeningSelection(option.id, 'confirmed')"
                >
                  Confirmee
                </button>
                <button
                  type="button"
                  class="planning__selection-option"
                  :class="{ 'planning__selection-option--active': option.selection_status === 'rejected' }"
                  :aria-pressed="option.selection_status === 'rejected'"
                  @click="toggleScreeningSelection(option.id, 'rejected')"
                >
                  Ignoree
                </button>
              </div>
            </article>
          </div>
        </div>

        <div v-if="detailScreening.isRecommended || detailScreening.isMustLock" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Pourquoi cette seance ressort</p>
          <ul class="planning__detail-list">
            <li v-if="detailScreening.isMustLock">il ne reste qu une seule seance valable pour ce film prioritaire</li>
            <li v-for="reason in detailScreening.recommendationReasons" :key="reason">{{ reason }}</li>
          </ul>
        </div>

        <div v-if="detailScreening.film?.synopsis" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Synopsis</p>
          <p>{{ detailScreening.film.synopsis }}</p>
        </div>

        <div v-if="detailScreening.film?.cast" class="planning__detail-copy">
          <p class="planning__detail-copy-title">Casting</p>
          <p>{{ detailScreening.film.cast }}</p>
        </div>

        <div v-if="detailScreening.film?.festival_url || detailScreening.film?.imdb_url || detailScreening.ticket_url" class="planning__links">
          <a v-if="detailScreening.film?.festival_url" :href="detailScreening.film.festival_url" target="_blank" rel="noopener">Ouvrir la fiche NIFFF</a>
          <a v-if="detailScreening.film?.imdb_url" :href="detailScreening.film.imdb_url" target="_blank" rel="noopener">IMDb</a>
          <a v-if="detailScreening.ticket_url" :href="detailScreening.ticket_url" target="_blank" rel="noopener">Billetterie</a>
        </div>
      </aside>
    </section>
  </section>
</template>
