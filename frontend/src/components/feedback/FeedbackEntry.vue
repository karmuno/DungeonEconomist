<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFeedbackStore } from '../../stores/feedback'

const fb = useFeedbackStore()
const button = ref<HTMLButtonElement | null>(null)

const statusLine = computed(() => {
  const n = fb.sentThisSession
  return n === 0 ? '' : `${n} report${n === 1 ? '' : 's'} sent this session`
})
</script>

<template>
  <div class="feedback-entry">
    <button ref="button" type="button" class="btn btn-secondary btn-sm entry-btn" @click="fb.open(button)">
      ⚑ Submit Feedback
    </button>
    <div v-if="statusLine" class="status">{{ statusLine }}</div>
  </div>
</template>

<style scoped>
.feedback-entry {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #374151;
}

.entry-btn {
  width: 100%;
  color: #9ca3af;
}

.status {
  font-size: 10px;
  color: #4b5563;
  line-height: 1.5;
}
</style>
