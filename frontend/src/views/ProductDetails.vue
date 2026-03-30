<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-4xl">
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">Product Profile</p>
          <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Product Details</h2>
          <p class="mt-2 text-sm text-slate-600 sm:text-base">
            Inspect the blockchain label and generate a QR snapshot.
          </p>
        </div>
        <router-link to="/products">
          <button class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700">
            Back To Products
          </button>
        </router-link>
      </div>

      <div class="rounded-2xl border border-emerald-100 bg-white/80 p-6 shadow-xl shadow-emerald-100/60 backdrop-blur sm:p-8">
        <div v-if="loading" class="text-sm text-slate-500">
          Loading Product Details...
        </div>
        <div v-else class="space-y-6">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">ID</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">{{ product.id }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Sender (User ID/Public Key)</p>
              <p class="mt-2 break-all text-sm font-medium text-slate-900">{{ product.sender }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Receiver (User ID/Public Key)</p>
              <p class="mt-2 break-all text-sm font-medium text-slate-900">{{ product.receiver }}</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Status</p>
              <p class="mt-2 text-sm text-slate-700">Sent: {{ product.sent ? 'Yes' : 'No' }}</p>
              <p class="text-sm text-slate-700">Received: {{ product.received ? 'Yes' : 'No' }}</p>
            </div>
            <div v-if="product.data" class="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm sm:col-span-2">
              <p class="text-xs uppercase tracking-[0.25em] text-slate-500">Data</p>
              <p class="mt-2 break-words text-sm text-slate-700">{{ product.data }}</p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-200/70 transition hover:bg-emerald-700"
              @click="handleGenerate"
            >
              Generate QR
            </button>
          </div>
        </div>
      </div>

      <div v-if="product.qrCodeUrl" class="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-lg">
        <div>
          <h3 class="text-xl font-semibold text-slate-900">Your QR Code</h3>
          <p class="mt-1 text-sm text-slate-600">Download and share the verified label.</p>
        </div>
        <img :src="product.qrCodeUrl" alt="QR Code" class="w-48 rounded-xl border border-slate-200 bg-white p-3 shadow-sm" />
        <a
          :href="product.qrCodeUrl"
          download="qrcode.png"
          class="inline-flex w-fit items-center justify-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          Download QR Code
        </a>
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
  name: 'ProductDetails',
  props: ['id'],
  data() {
    return {
      product: {
        id: this.id,
        sender: '',
        receiver: '',
        sent: false,
        received: false,
        data: '',
        qrCodeUrl: ''
      },
      loading: false,
      error: ''
    }
  },
  async created() {
    this.loading = true
    this.error = ''
    try {
      const response = await axios.get(`http://localhost:3001/api/blockchain/labels/${this.id}`)
      const data = response.data.label
      this.product = {
        id: data.id,
        sender: data.sender,
        receiver: data.receiver,
        sent: data.sent,
        received: data.received,
        data: data.data || ''
      }
    } catch (err) {
      console.error("Failed to fetch product details:", err)
      this.error = err.message || 'Failed to load product details.'
    } finally {
      this.loading = false
    }
  },
  methods: {
  async handleGenerate() {
      try {
        const typedData = `${this.product.id}||${this.product.sender}||${this.product.receiver}`
        const response = await axios.post('http://localhost:3000/api/generate_qr', { data: typedData })
        this.product.qrCodeUrl = response.data.qrCode
      } catch (error) {
        console.error('QR Code generation failed:', error)
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
</style>