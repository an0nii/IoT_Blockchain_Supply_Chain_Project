<template>
  <div class="page min-h-screen bg-gradient-to-br from-amber-50 via-white to-emerald-50 px-4 py-10">
    <div class="mx-auto max-w-5xl">
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.35em] text-emerald-600">Device Hub</p>
          <h2 class="title mt-2 text-3xl font-semibold text-slate-900 sm:text-4xl">Devices Overview</h2>
          <p class="mt-2 text-sm text-slate-600 sm:text-base">
            Keep track of registered devices and jump into details.
          </p>
        </div>
        <router-link to="/generate-qr">
          <button class="inline-flex items-center justify-center rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-300/50 transition hover:bg-slate-800">
            Generate QR Code For Product
          </button>
        </router-link>
      </div>

      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white/90 shadow-xl">
        <table class="min-w-full table-fixed">
          <thead class="bg-slate-900 text-white">
            <tr>
              <th class="w-1/5 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Name</th>
              <th class="w-1/5 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">User ID</th>
              <th class="w-1/5 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Public Key</th>
              <th class="w-1/5 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Role</th>
              <th class="w-1/5 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Details</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="device in devices" :key="device.id" class="bg-white/70">
              <td class="px-4 py-3 text-sm text-slate-700">{{ device.name }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">{{ device.userId }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">{{ device.publicKey }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">{{ device.role }}</td>
              <td class="px-4 py-3 text-sm text-slate-700">
                <router-link :to="`/device/${device.id}`">
                  <button class="inline-flex items-center justify-center rounded-full bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700">
                    View
                  </button>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const devices = ref([])

const fetchDevices = async () => {
  try {
    const res = await axios.get('http://localhost:3000/api/devices')
    devices.value = res.data.devices
  } catch (e) {
    console.error("Error fetching devices: ", e)
  }
}

const syncDevices = async () => {
  try {
    const storedDevices = localStorage.getItem("devices")
    if (storedDevices) {
      const localDevices = JSON.parse(storedDevices)
      for (const device of localDevices) {
        await axios.post('http://localhost:3000/api/devices', device)
      }
      localStorage.removeItem("devices")
    }
  } catch (e) {
    console.error("Error syncing devices: ", e)
  }
}

onMounted(async () => {
  await syncDevices()
  await fetchDevices()
})
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