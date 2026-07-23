<template>
  <div class="sghl-logo" :class="[`sghl-logo--${size}`, { 'sghl-logo--light': light }]">
    <svg class="sghl-logo__mark" viewBox="0 0 96 96" fill="none" aria-hidden="true">
      <defs>
        <linearGradient :id="gradId" x1="12" y1="8" x2="86" y2="90" gradientUnits="userSpaceOnUse">
          <stop stop-color="#1E3A8A" />
          <stop offset="1" stop-color="#0B1F4A" />
        </linearGradient>
      </defs>
      <circle cx="48" cy="48" r="46" :fill="light ? '#E8EEF9' : `url(#${gradId})`" />
      <circle
        cx="48"
        cy="48"
        r="38"
        :stroke="light ? '#1E3A8A' : '#93C5FD'"
        :stroke-opacity="light ? 0.25 : 0.35"
        stroke-width="2"
      />
      <rect x="42" y="26" width="12" height="44" rx="3" :fill="light ? '#0B1F4A' : '#F8FAFC'" />
      <rect x="26" y="42" width="44" height="12" rx="3" :fill="light ? '#0B1F4A' : '#F8FAFC'" />
      <path
        d="M22 62h10l4-8 6 14 5-10h27"
        :stroke="light ? '#2563EB' : '#60A5FA'"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
      />
    </svg>
    <div v-if="showWordmark" class="sghl-logo__text">
      <span class="sghl-logo__name">SGHL</span>
      <span v-if="tagline" class="sghl-logo__tag">{{ tagline }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: { type: String, default: 'md' },
  light: { type: Boolean, default: false },
  showWordmark: { type: Boolean, default: true },
  tagline: { type: String, default: '' },
})

const gradId = computed(() => `sghlBlue_${props.light ? 'L' : 'D'}_${props.size}`)
</script>

<style scoped>
.sghl-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.85rem;
  min-width: 0;
}
.sghl-logo__mark {
  flex-shrink: 0;
  display: block;
  filter: drop-shadow(0 8px 18px rgba(11, 31, 74, 0.28));
}
.sghl-logo--sm .sghl-logo__mark { width: 36px; height: 36px; }
.sghl-logo--md .sghl-logo__mark { width: 44px; height: 44px; }
.sghl-logo--lg .sghl-logo__mark { width: 56px; height: 56px; }
.sghl-logo--xl .sghl-logo__mark { width: 76px; height: 76px; }

.sghl-logo__text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}
.sghl-logo__name {
  font-family: var(--font-display, 'Sora', sans-serif);
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1;
  color: #0b1f4a;
}
.sghl-logo--light .sghl-logo__name {
  color: #f8fafc;
}
.sghl-logo--sm .sghl-logo__name { font-size: 1.05rem; }
.sghl-logo--md .sghl-logo__name { font-size: 1.25rem; }
.sghl-logo--lg .sghl-logo__name { font-size: 1.55rem; }
.sghl-logo--xl .sghl-logo__name { font-size: 2rem; }

.sghl-logo__tag {
  font-family: var(--font-body, 'Figtree', sans-serif);
  font-size: 0.72rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sghl-logo--light .sghl-logo__tag { color: rgba(226, 232, 240, 0.78); }
</style>
