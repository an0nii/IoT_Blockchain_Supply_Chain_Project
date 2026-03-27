<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="app-header__inner">
        <div>
          <p class="app-eyebrow">Supply Chain</p>
          <h1 class="app-title">Control Panel</h1>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <router-link to="/add-device" v-if="showAddButton">
            <button class="app-btn app-btn--primary">Add Device</button>
          </router-link>

          <router-link to="/products" v-if="showProductsButton">
            <button class="app-btn app-btn--ghost">Products</button>
          </router-link>
        </div>
      </div>
    </header>
    <main class="p-4 sm:p-6">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    showAddButton() {
      return this.$route.path !== '/add-device';
    },
    showProductsButton() {
      return this.$route.path !== '/products';
    }
  },
}
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Space+Grotesk:wght@400;500;600;700&display=swap");

.app-shell {
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  min-height: 100vh;
  background: radial-gradient(circle at top, rgba(16, 185, 129, 0.12), transparent 55%),
    linear-gradient(120deg, rgba(251, 191, 36, 0.08), rgba(16, 185, 129, 0.08));
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(18px);
  background: rgba(255, 255, 255, 0.75);
  border-bottom: 1px solid rgba(16, 185, 129, 0.2);
}

.app-header__inner {
  max-width: 72rem;
  margin: 0 auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.app-eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.35em;
  color: #059669;
  margin-bottom: 0.4rem;
}

.app-title {
  font-family: "Fraunces", "Times New Roman", serif;
  font-size: 1.6rem;
  color: #0f172a;
}

.app-btn {
  border-radius: 9999px;
  padding: 0.55rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.app-btn--primary {
  background: #059669;
  color: #fff;
  box-shadow: 0 14px 28px rgba(16, 185, 129, 0.25);
}

.app-btn--primary:hover {
  background: #047857;
}

.app-btn--ghost {
  background: #fff;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.12);
}

.app-btn--ghost:hover {
  border-color: rgba(5, 150, 105, 0.35);
  color: #047857;
}

@media (max-width: 640px) {
  .app-header__inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>