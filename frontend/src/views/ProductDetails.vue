<template>
  <div class="max-w-2xl mx-auto mt-8 p-6 bg-white rounded shadow">
    <h2 class="text-2xl font-semibold mb-6">Product Details</h2>
    <div v-if="loading" class="mb-4 text-gray-600">
      Loading Product Details...
    </div>
    <div v-else>
      <div class="mb-6">
        <p class="mb-2"><strong>ID:</strong> {{ product.id }}</p>
        <p class="mb-2"><strong>Sender Address:</strong> {{ product.sender }}</p>
        <p class="mb-2"><strong>Receiver Address:</strong> {{ product.receiver }}</p>
        <p class="mb-2"><strong>Sent:</strong> {{ product.sent ? 'Yes' : 'No' }}</p>
        <p class="mb-2"><strong>Received:</strong> {{ product.received ? 'Yes' : 'No' }}</p>
        <p class="mb-2"><strong>Voided:</strong> {{ product.voided ? 'Yes' : 'No' }}</p>
        <p v-if="product.description" class="mb-2"><strong>Description:</strong> {{ product.description }}</p>
      </div>
      <div class="flex justify-between items-center">
        <button
          type="button"
          class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 mr-4"
          @click="handleGenerate"
        >
          Generate QR
        </button>
        <router-link to="/products">
          <button class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
            Back To Products
          </button>
        </router-link>
      </div>
    </div>
    <div v-if="product.qrCodeUrl" class="mt-6">
      <h3 class="text-xl font-semibold mb-2">Your QR Code:</h3>
      <img :src="product.qrCodeUrl" alt="QR Code" class="border p-2" />
      <a
        :href="product.qrCodeUrl"
        download="qrcode.png"
        class="mt-4 inline-block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Download QR Code
      </a>
    </div>
    <div v-if="error" class="mt-4 p-2 bg-red-200 text-red-800 rounded">
      {{ error }}
    </div>
  </div>
</template>

<script>
import { ethers, BrowserProvider } from 'ethers'
import IOTContractMonitoring from '../../IOTContractMonitoring.json'
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
        voided: false,
        description: '',
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
      if (!window.ethereum) {
        throw new Error('MetaMask not installed')
      }
      const provider = new BrowserProvider(window.ethereum)
      const contract = new ethers.Contract(IOTContractMonitoring.address, IOTContractMonitoring.abi, provider)
      const data = await contract.labels(this.id)
      this.product = {
        id: data.id.toString(),
        sender: data.sender,
        receiver: data.receiver,
        sent: data.sent,
        received: data.received,
        voided: data.voided,
        description: data.description ? data.description : ''
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
</style>