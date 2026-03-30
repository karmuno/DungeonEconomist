<script setup lang="ts">
import { useTutorialStore } from '../../stores/tutorial'

const tutorial = useTutorialStore()
</script>

<template>
  <Teleport to="body">
    <!-- Minimized: small floating button -->
    <button
      v-if="!tutorial.isTutorialComplete && tutorial.currentHint && tutorial.minimized"
      class="tutorial-minimized"
      @click="tutorial.restore()"
    >
      ?
    </button>

    <!-- Full popup -->
    <div
      v-if="!tutorial.isTutorialComplete && tutorial.currentHint && !tutorial.minimized"
      class="tutorial-overlay"
    >
      <div class="tutorial-popup">
        <div class="tutorial-header">
          <span class="tutorial-title">Tutorial</span>
          <span class="tutorial-step">{{ tutorial.currentStep + 1 }} / 7</span>
        </div>
        <p class="tutorial-message">{{ tutorial.currentHint }}</p>
        <div class="tutorial-actions">
          <button class="tutorial-btn tutorial-btn-primary" @click="tutorial.dismiss()">Got it</button>
          <button class="tutorial-btn tutorial-btn-secondary" @click="tutorial.minimize()">Minimize</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.tutorial-popup {
  background: var(--bg-primary, #1a1a2e);
  border: 2px solid #fbbf24;
  border-radius: 8px;
  padding: 20px 24px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 0 30px rgba(251, 191, 36, 0.15);
}

.tutorial-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.tutorial-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: #fbbf24;
}

.tutorial-step {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.tutorial-message {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary, #eee);
  margin: 0 0 16px;
}

.tutorial-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.tutorial-btn {
  padding: 5px 16px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}

.tutorial-btn-primary {
  background: #fbbf24;
  color: #000;
  border-color: #fbbf24;
}

.tutorial-btn-primary:hover {
  background: #f59e0b;
}

.tutorial-btn-secondary {
  background: none;
  color: var(--text-muted);
  border-color: var(--border-color, #333);
}

.tutorial-btn-secondary:hover {
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.tutorial-minimized {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 100000;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fbbf24;
  color: #000;
  font-size: 16px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(251, 191, 36, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tutorial-minimized:hover {
  background: #f59e0b;
  transform: scale(1.1);
}
</style>
