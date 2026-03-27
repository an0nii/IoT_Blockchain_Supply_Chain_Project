<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-5xl">
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">Product Ledger</p>
          <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Products List</h2>
          <p class="mt-2 text-sm text-slate-600 sm:text-base">
            Monitor blockchain product states in real time.
          </p>
        </div>
        <router-link to="/">
          <button class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700">
            Home Page
          </button>
        </router-link>
      </div>

      <div v-if="error" class="mb-6 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {{ error }}
      </div>

      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white/90 shadow-xl">
        <table class="min-w-full table-fixed">
          <thead class="bg-slate-900 text-white">
            <tr>
              <th class="w-1/4 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">ID</th>
              <th class="w-1/4 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Sent</th>
              <th class="w-1/4 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Received</th>
              <th class="w-1/4 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Details</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="(product, index) in products" :key="index" class="bg-white/70">
              <td class="px-4 py-3 text-sm text-slate-700">{{ product.id }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">{{ product.sent ? 'Yes' : 'No' }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">{{ product.received ? 'Yes' : 'No' }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">
                <router-link :to="`/product/${product.id}`">
                  <button class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700">
                    View
                  </button>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="loading" class="mt-4 text-sm text-slate-500">
        Loading...
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProductList',
  data() {
    return {
      products: [],
      loading: false,
      error: '',
      intervalId: null
    }
  },
  methods: {
    async fetchProducts() {
      this.loading = true
      this.error = ''
      try {
        const response = await axios.get('http://localhost:3001/api/blockchain/labels')
        const products = response.data.labels || []
        this.products = products
        sessionStorage.setItem("cachedProducts", JSON.stringify(products))
      } catch (e) {
        this.error = e.message || "Failed to fetch products."
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.fetchProducts()
    this.intervalId = setInterval(() => {
      this.fetchProducts()
    }, 5000)
    const cached = sessionStorage.getItem("cachedProducts")
    if (cached) {
      this.products = JSON.parse(cached)
    }
  },
  beforeUnmount() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
    }
  }
}
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Space+Grotesk:wght@400;500;600;700&display=swap");

.page {
  --accent: #059669;
  --accent-soft: #d1fae5;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

.title {
  font-family: "Fraunces", "Times New Roman", serif;
}

table {
  table-layout: fixed;
  border-collapse: collapse;
}
</style>