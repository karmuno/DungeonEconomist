<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useFeedbackStore } from '../../stores/feedback'
import * as feedbackApi from '../../api/feedback'
import { FEEDBACK_CATEGORIES, type FeedbackCategory } from '../../types'

// Copy below is from the design handoff (design_handoff_feedback_form/README.md).
const SEVERITY = [
  { n: 1, title: 'Barely', desc: "I don't care if this issue is ever addressed." },
  { n: 2, title: 'Somewhat', desc: 'It would be nice to see this issue get addressed.' },
  { n: 3, title: 'Very', desc: 'I would have a lot more fun if this issue were addressed.' },
  { n: 4, title: 'Critically', desc: "I won't or can't play the game until the issue is addressed." },
] as const

const auth = useAuthStore()
const fb = useFeedbackStore()

const category = ref<FeedbackCategory | ''>('')
const doing = ref('')
const feedback = ref('')
const name = ref('')
const severity = ref<number | null>(null)
const hoverSeverity = ref<number | null>(null)
const submitting = ref(false)
const error = ref('')
const submitted = ref(false)
const last = ref<{ id: number; category: string; severity: number | null } | null>(null)
const categorySelect = ref<HTMLSelectElement | null>(null)

const showName = computed(() => !auth.isLoggedIn)

const canSubmit = computed(
  () => category.value !== '' && doing.value.trim().length > 0 && feedback.value.trim().length > 0 && !submitting.value,
)

const thanksLine = computed(() =>
  fb.sentThisSession > 1
    ? `Logged. That is ${fb.sentThisSession} this session — you are doing the cohort a real favour.`
    : 'Logged. Keep them coming — every report makes the next build sharper.',
)

const receiptLine = computed(() =>
  last.value ? `feedback #${last.value.id} · ${last.value.category} · severity ${last.value.severity ?? '—'}` : '',
)

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

async function focusCategory() {
  await nextTick()
  categorySelect.value?.focus()
}

watch(
  () => fb.isOpen,
  (open) => {
    if (open) {
      submitted.value = false
      error.value = ''
      document.addEventListener('keydown', onKeydown)
      focusCategory()
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  },
)

onUnmounted(() => document.removeEventListener('keydown', onKeydown))

function close() {
  fb.close()
}

function pick(n: number) {
  severity.value = severity.value === n ? null : n
}

function sevClass(n: number) {
  if (severity.value === n) return 'selected'
  if (hoverSeverity.value === n) return 'hot'
  return ''
}

function resetForm() {
  category.value = ''
  doing.value = ''
  feedback.value = ''
  name.value = ''
  severity.value = null
  hoverSeverity.value = null
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const res = await feedbackApi.submit({
      category: category.value as FeedbackCategory,
      doing: doing.value.trim(),
      feedback: feedback.value.trim(),
      severity: severity.value,
      name: showName.value && name.value.trim() ? name.value.trim() : null,
      page_url: window.location.href,
    })
    // Receipt is a snapshot: the fields are cleared right after.
    last.value = { id: res.id, category: category.value, severity: severity.value }
    fb.sentThisSession++
    resetForm()
    submitted.value = true
  } catch {
    error.value = 'Submission failed. Try again.'
  } finally {
    submitting.value = false
  }
}

function another() {
  submitted.value = false
  focusCategory()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="fb.isOpen" class="modal-overlay" @click.self="close">
      <div class="modal-content feedback-panel" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
        <div class="feedback-header">
          <h3 id="feedback-title">Submit Feedback</h3>
          <button type="button" class="close-btn" aria-label="Close" @click="close">×</button>
        </div>

        <div class="feedback-body">
          <form v-if="!submitted" class="feedback-form" @submit.prevent="submit">
            <div>
              <div class="field-label">What kind of feedback is this? <span class="req">*</span></div>
              <select ref="categorySelect" v-model="category" class="form-select field-control" required>
                <option value="">Choose one…</option>
                <option v-for="c in FEEDBACK_CATEGORIES" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>

            <div>
              <div class="field-label">What were you doing? <span class="req">*</span></div>
              <input
                v-model="doing"
                class="form-input field-control"
                type="text"
                placeholder="e.g. &quot;Sending my party into the dungeon&quot;"
                required
              />
            </div>

            <div>
              <div class="field-label">What's your feedback? <span class="req">*</span></div>
              <textarea v-model="feedback" class="form-input field-control field-textarea" rows="3" required></textarea>
            </div>

            <div>
              <div class="field-label">How important is this feedback?</div>
              <div class="severity-grid">
                <div v-for="opt in SEVERITY" :key="opt.n" class="severity-cell">
                  <button
                    type="button"
                    class="severity-btn"
                    :class="sevClass(opt.n)"
                    :aria-pressed="severity === opt.n"
                    @click="pick(opt.n)"
                    @mouseenter="hoverSeverity = opt.n"
                    @mouseleave="hoverSeverity = null"
                  >{{ opt.n }}</button>
                  <span class="severity-title" :class="sevClass(opt.n)">{{ opt.title }}</span>
                  <span class="severity-desc" :class="sevClass(opt.n)">{{ opt.desc }}</span>
                </div>
              </div>
            </div>

            <div v-if="showName">
              <div class="field-label field-label-row">
                <span>Name</span>
                <span class="optional">Optional</span>
              </div>
              <input
                v-model="name"
                class="form-input field-control"
                type="text"
                placeholder="So we can follow up — or leave it blank."
              />
            </div>

            <div v-if="error" class="error-line">{{ error }}</div>

            <div class="actions">
              <button type="button" class="btn btn-secondary action-secondary" @click="close">Cancel</button>
              <button type="submit" class="btn btn-primary action-primary" :disabled="!canSubmit">Submit Feedback</button>
            </div>
          </form>

          <div v-else class="thanks">
            <div class="thanks-headline">Thanks!</div>
            <div class="thanks-line">{{ thanksLine }}</div>
            <div class="receipt">{{ receiptLine }}</div>
            <div class="actions">
              <button type="button" class="btn btn-secondary action-secondary" @click="another">Submit Another</button>
              <button type="button" class="btn btn-primary action-primary" @click="close">Back to the Keep</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.feedback-panel {
  max-width: 560px;
}

.feedback-header {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  background-color: #111827;
  border-bottom: 1px solid var(--border-color);
}

.feedback-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--accent-green);
}

.close-btn {
  background: none;
  border: none;
  padding: 0;
  font-family: inherit;
  font-size: 1.25rem;
  line-height: 1;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.feedback-body {
  padding: 1rem;
}

.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-label {
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.field-label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.req {
  color: var(--accent-red);
}

.optional {
  font-size: 10px;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.field-control {
  box-sizing: border-box;
}

.field-textarea {
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
}

.severity-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.severity-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.severity-btn {
  width: 100%;
  height: 38px;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  color: #9ca3af;
  background-color: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}

.severity-btn.hot {
  color: var(--accent-green);
  background-color: rgba(74, 222, 128, 0.08);
  border-color: var(--accent-green);
}

.severity-btn.selected {
  color: #000;
  background-color: var(--accent-green-dark);
  border-color: var(--accent-green-dark);
}

.severity-title {
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  line-height: 1.3;
  color: #9ca3af;
  transition: color 0.12s;
}

.severity-title.hot,
.severity-title.selected {
  color: var(--accent-green);
}

.severity-desc {
  font-size: 10px;
  text-align: center;
  line-height: 1.35;
  text-wrap: pretty;
  color: var(--text-muted);
  transition: color 0.12s;
}

.severity-desc.selected {
  color: #9ca3af;
}

.error-line {
  font-size: 11px;
  color: var(--accent-red);
}

.actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 2px;
}

.action-secondary {
  color: #9ca3af;
}

.action-primary {
  background-color: var(--accent-green-dim);
  border-color: var(--accent-green-dim);
}

.action-primary:hover:not(:disabled) {
  background-color: var(--accent-green-dark);
  border-color: var(--accent-green-dark);
}

.thanks {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 8px 0;
}

.thanks-headline {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--accent-green);
}

.thanks-line {
  font-size: 13px;
  line-height: 1.6;
  color: #9ca3af;
}

.receipt {
  padding: 10px 12px;
  font-size: 11px;
  line-height: 1.7;
  color: var(--text-muted);
  background-color: rgba(74, 222, 128, 0.06);
  border: 1px solid var(--accent-green-dim);
  border-radius: var(--border-radius);
}
</style>
