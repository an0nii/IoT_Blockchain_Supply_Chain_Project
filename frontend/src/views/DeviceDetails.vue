<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-4xl">
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">Device Snapshot</p>
          <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Device Details</h2>
          <p class="mt-2 text-sm text-slate-600 sm:text-base">
            Review device identity and related blockchain products.
          </p>
        </div>
        <router-link to="/">
          <button class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700">
            Home Page
          </button>
        </router-link>
      </div>

      <div class="rounded-2xl border border-emerald-100 bg-white/80 p-6 shadow-xl shadow-emerald-100/60 backdrop-blur sm:p-8">
        <div v-if="device" class="space-y-6">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Name</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ device.name }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">User ID</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ device.userId }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Public Key</p>
              <p class="mt-2 break-all text-sm font-medium text-slate-900">{{ device.publicKey }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Role</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ device.role }}</p>
            </div>
            <div v-if="device.description" class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm sm:col-span-2">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Description</p>
              <p class="mt-2 text-sm text-slate-700">{{ device.description }}</p>
            </div>
          </div>

          <div>
            <div class="mb-4 flex items-center justify-between">
              <h3 class="text-xl font-semibold text-slate-900">Related Products</h3>
              <span class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                {{ relatedProducts.length }} items
              </span>
            </div>
            <div v-if="loadingProducts" class="text-sm text-slate-500">
              Loading related products...
            </div>
            <div v-else class="overflow-hidden rounded-2xl border border-slate-200 bg-white/90">
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
                  <tr v-for="(product, index) in relatedProducts" :key="index" class="bg-white/70">
                    <td class="px-4 py-3 text-sm text-slate-700">{{ product.id }}</td>
                    <td class="px-4 py-3 text-sm text-slate-700">{{ product.sent ? 'Yes' : 'No' }}</td>
                    <td class="px-4 py-3 text-sm text-slate-700">{{ product.received ? 'Yes' : 'No' }}</td>
                    <td class="px-4 py-3 text-sm text-slate-700">
                      <router-link :to="`/product/${product.id}`">
                        <button class="inline-flex items-center justify-center rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800">
                          View
                        </button>
                      </router-link>
                    </td>
                  </tr>
                  <tr v-if="relatedProducts.length === 0">
                    <td colspan="4" class="px-4 py-6 text-center text-sm text-slate-500">
                      No related products found.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-slate-500">
          Device not found.
        </div>
      </div>

      <div v-if="error" class="mt-6 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: "DeviceDetails",
  props: ['id'],
  data() {
    return {
      device: null,
      error: '',
      relatedProducts: [],
      loadingProducts: false,
      errorProducts: ''
    }
  },
  async created() {
    try {
      const res = await axios.get('http://localhost:3000/api/devices')
      const devices = res.data.devices
      this.device = devices.find(d => String(d.id) === String(this.id))
      if (!this.device) {
        this.error = "Device not found."
      } else {
        this.fetchRelatedProducts()
      }
    } catch (e) {
      this.error = e.message || "Error loading device details."
    }
  },
  methods: {
    fetchRelatedProducts() {
      this.loadingProducts = true;
      try {
        let products = []
        const storedProducts = sessionStorage.getItem("cachedProducts")
        if (storedProducts) {
          products = JSON.parse(storedProducts)
        }
        // Фильтрация по userId или publicKey
        const deviceUserId = (this.device.userId || '').trim().toLowerCase();
        const devicePublicKey = (this.device.publicKey || '').trim().toLowerCase();
        this.relatedProducts = products.filter(product => {
          const sender = (product.sender || '').trim().toLowerCase();
          const receiver = (product.receiver || '').trim().toLowerCase();
          return sender === deviceUserId || receiver === deviceUserId || sender === devicePublicKey || receiver === devicePublicKey;
        })
      } catch (e) {
        this.errorProducts = e.message || "Failed to load related products."
      } finally {
        this.loadingProducts = false;
      }
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