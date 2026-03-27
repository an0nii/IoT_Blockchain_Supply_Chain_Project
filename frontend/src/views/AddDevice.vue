<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-2xl">
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">Device Registry</p>
          <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Add Device</h2>
          <p class="mt-2 max-w-xl text-sm text-slate-600 sm:text-base">
            Register a trusted IoT device and sync it with the blockchain authorization flow.
          </p>
        </div>
        <div class="hidden h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-sm font-semibold text-white shadow-lg shadow-emerald-200/70 sm:flex">
          IOT
        </div>
      </div>

      <div class="rounded-2xl border border-emerald-100 bg-white/80 shadow-xl shadow-emerald-100/60 backdrop-blur">
        <form @submit.prevent="handleSubmit" class="space-y-6 p-6 sm:p-8">
          <div>
            <label class="text-sm font-medium text-slate-700">Device Name</label>
            <input
              type="text"
              v-model="device.name"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              placeholder="Type a device name"
              required
            />
          </div>

          <div>
            <label class="text-sm font-medium text-slate-700">Device Type</label>
            <select
              v-model="device.type"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              required
            >
              <option value="" disabled selected>Select Device Type</option>
              <option value="Sender">Sender</option>
              <option value="Receiver">Receiver</option>
            </select>
          </div>

          <div>
            <label class="text-sm font-medium text-slate-700">Device Adress</label>
            <input
              type="text"
              v-model="device.address"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              placeholder="Enter device address"
              required
            />
          </div>

          <div>
            <label class="text-sm font-medium text-slate-700">Description</label>
            <textarea
              v-model="device.description"
              class="mt-2 w-full rounded-lg border border-slate-200 bg-white/80 px-4 py-2.5 text-slate-800 shadow-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
              placeholder="Type a description"
              rows="4"
            ></textarea>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3">
            <button
              type="submit"
              class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-200/70 transition hover:bg-emerald-700"
            >
              Save
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

      <div v-if="deviceError" class="mt-6 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {{ deviceError }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'AddDevice',
  data() {
    return {
      device: {
        name: '',
        type: '',
        address: '',
        description: ''
      },
      deviceError: '',
    }
  },
  methods: {
    async handleSubmit() {
      try {
        const _account = this.device.address
        const _asSender = this.device.type === 'Sender'
        const _asReceiver = this.device.type === 'Receiver'
        const _status = true
        await axios.post('http://localhost:3001/api/blockchain/authorize-iot', {
          account: _account,
          asSender: _asSender,
          asReceiver: _asReceiver,
          status: _status,
        })
        let devices = []
        const storedDevices = localStorage.getItem('devices')
        if (storedDevices) {
          devices = JSON.parse(storedDevices)
        }
        const newDevice = { ...this.device, id: Date.now() }
        devices.push(newDevice)
        localStorage.setItem('devices', JSON.stringify(devices))
        console.log('Device added:', newDevice)
        this.device.name = ''
        this.device.type = ''
        this.device.address = ''
        this.device.description = ''        
        this.$router.push('/')
      } catch (error) {
        console.error('Error adding device:', error)
        this.deviceError = error.message
      }
    },
  },
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