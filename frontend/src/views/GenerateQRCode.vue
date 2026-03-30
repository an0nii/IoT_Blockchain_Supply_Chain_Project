<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-2xl">
      <div class="mb-8">
        <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">QR Studio</p>
        <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Generate Product QR Code</h2>
        <p class="mt-2 text-sm text-slate-600 sm:text-base">
          Build a secure QR payload and optionally send it to the contract.
        </p>
      </div>

      <div class="rounded-2xl border border-emerald-100 bg-white/80 shadow-xl shadow-emerald-100/60 backdrop-blur">
        <form @submit.prevent="handleGenerate" class="space-y-6 p-6 sm:p-8">
          <div>
            <label class="text-sm font-medium text-slate-700">Sender (User ID или Public Key)</label>
            <input
              type="text"
              v-model="senderId"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              placeholder="Введите User ID или Public Key отправителя"
              required
            />
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700">Receiver (User ID или Public Key)</label>
            <input
              type="text"
              v-model="receiverId"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              placeholder="Введите User ID или Public Key получателя"
              required
            />
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <button
              type="submit"
              class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-200/70 transition hover:bg-emerald-700"
            >
              Generate QR
            </button>
            <router-link to="/">
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-emerald-200 hover:text-emerald-700"
              >
                Home Page
              </button>
            </router-link>
          </div>
        </form>
      </div>

      <div v-if="qrCodeUrl" class="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white/90 p-6 shadow-lg">
        <div>
          <h3 class="text-xl font-semibold text-slate-900">Your QR Code</h3>
          <p class="mt-1 text-sm text-slate-600">Ready to download or push to the contract.</p>
        </div>
        <img :src="qrCodeUrl" alt="QR Code" class="w-48 rounded-xl border border-slate-200 bg-white p-3 shadow-sm" />
        <a
          :href="qrCodeUrl"
          download="qrcode.png"
          class="inline-flex w-fit items-center justify-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          Download QR Code
        </a>
      </div>

      <div v-if="pendingProductId" class="mt-6">
        <button
          @click="sendToContract"
          class="inline-flex items-center justify-center rounded-full bg-amber-500 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-amber-200/70 transition hover:bg-amber-600"
        >
          Send To Contract
        </button>
      </div>

      <div v-if="contractError" class="mt-6 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {{ contractError }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'GenerateQRCode',
  data() {
    return {
      senderId: '',
      receiverId: '',
      qrCodeUrl: '',
      currentProductId: null,
      pendingProductId: null,
      contractError: ''
    }
  },
  created() {
    if (!localStorage.getItem("currentId")) {
      localStorage.setItem("currentId", 1)
    }
  },
  methods: {
    getCurrentId() {
      let currentId = localStorage.getItem("currentId")
      return parseInt(currentId, 10)
    },
    incrementCurrentId() {
      let currentId = this.getCurrentId()
      currentId++
      localStorage.setItem("currentId", currentId)
      return currentId
    },
    async handleGenerate() {
      try {
        const productId = this.getCurrentId()
        this.pendingProductId = productId
        const typedData = `${productId}||${this.senderId}||${this.receiverId}`
        const response = await axios.post('http://localhost:3000/api/generate_qr', { data: typedData })
        this.qrCodeUrl = response.data.qrCode
      } catch (error) {
        console.error('QR Code generation failed:', error)
      }
    },
    async sendToContract() {
      try {
        this.contractError = ''
        console.log("Sending transaction with parameters:", {
          productId: this.pendingProductId,
          sender: this.senderId,
          receiver: this.receiverId
        })
        const dataPayload = `${this.pendingProductId}||${this.senderId}||${this.receiverId}`
        await axios.post('http://localhost:3001/api/blockchain/labels', {
          labelId: String(this.pendingProductId),
          sender: this.senderId,
          receiver: this.receiverId,
          data: dataPayload,
        })
        this.currentProductId = this.pendingProductId
        this.incrementCurrentId()
      } catch (error) {
        console.error("Transaction failed:", error)
        if (error?.response?.data?.error?.includes("sender not authorized")) {
          this.contractError = "Transaction failed: sender is not authorized to perform this operation."
        } else {
          this.contractError = error?.response?.data?.error || error.message
        }
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