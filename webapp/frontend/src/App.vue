<template>
  <div class="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
    <div class="container mx-auto px-4 py-8">
      <!-- Header -->
      <header class="text-center mb-12">
        <h1 class="text-4xl font-bold text-purple-900 mb-2">
          Mastodon Quotability Manager
        </h1>
        <p class="text-gray-600">
          Enable quote posts for all your Mastodon content
        </p>
      </header>

      <!-- Main Content -->
      <div class="max-w-2xl mx-auto">
        <!-- Error Alert -->
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          <div class="flex items-start">
            <svg class="w-5 h-5 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            <span>{{ error }}</span>
          </div>
        </div>

        <!-- Success Alert -->
        <div v-if="success" class="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">
          <div class="flex items-start">
            <svg class="w-5 h-5 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <span>{{ success }}</span>
          </div>
        </div>

        <!-- Step 1: Connect to Instance -->
        <div v-if="step === 'connect'" class="bg-white rounded-lg shadow-lg p-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">
            Connect to your Mastodon instance
          </h2>
          <p class="text-gray-600 mb-6">
            Enter your Mastodon instance URL to get started
          </p>

          <form @submit.prevent="startAuth">
            <div class="mb-4">
              <label for="instance" class="block text-sm font-medium text-gray-700 mb-2">
                Instance URL
              </label>
              <input
                v-model="instanceUrl"
                type="text"
                id="instance"
                placeholder="mastodon.social"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
              <p class="mt-2 text-sm text-gray-500">
                Enter just the domain (e.g., mastodon.social) or full URL
              </p>
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ loading ? 'Connecting...' : 'Connect' }}
            </button>
          </form>
        </div>

        <!-- Step 2: Authorize -->
        <div v-if="step === 'authorize'" class="bg-white rounded-lg shadow-lg p-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">
            Authorize the application
          </h2>
          <p class="text-gray-600 mb-6">
            Click the button below to authorize this application with your Mastodon instance.
            After authorizing, you'll receive a code to paste back here.
          </p>

          <a
            :href="authUrl"
            target="_blank"
            class="block w-full bg-blue-600 text-white text-center py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition mb-6"
          >
            Open Authorization Page
          </a>

          <form @submit.prevent="completeAuth">
            <div class="mb-4">
              <label for="authCode" class="block text-sm font-medium text-gray-700 mb-2">
                Authorization Code
              </label>
              <input
                v-model="authCode"
                type="text"
                id="authCode"
                placeholder="Paste the code here"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ loading ? 'Verifying...' : 'Continue' }}
            </button>
          </form>
        </div>

        <!-- Step 3: Account Info -->
        <div v-if="step === 'account'" class="bg-white rounded-lg shadow-lg p-8">
          <div v-if="accountInfo">
            <div class="text-center mb-6">
              <h2 class="text-2xl font-semibold text-gray-800 mb-2">
                {{ accountInfo.display_name }}
              </h2>
              <p class="text-gray-600">@{{ accountInfo.username }}</p>
              <a :href="accountInfo.url" target="_blank" class="text-blue-600 hover:underline text-sm">
                View Profile
              </a>
            </div>

            <div class="bg-gray-50 rounded-lg p-4 mb-6">
              <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div class="text-2xl font-bold text-purple-600">{{ accountInfo.posts_count }}</div>
                  <div class="text-sm text-gray-600">Posts</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-purple-600">{{ accountInfo.followers_count }}</div>
                  <div class="text-sm text-gray-600">Followers</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-purple-600">{{ accountInfo.following_count }}</div>
                  <div class="text-sm text-gray-600">Following</div>
                </div>
              </div>
            </div>

            <div class="mb-6">
              <h3 class="text-lg font-semibold text-gray-800 mb-3">
                Enable Quotability
              </h3>
              <p class="text-gray-600 mb-4">
                This will update <strong>all {{ accountInfo.posts_count }} posts</strong> to allow quoting.
                This is a one-time operation.
              </p>

              <div class="mb-4">
                <label for="policy" class="block text-sm font-medium text-gray-700 mb-2">
                  Quote Policy
                </label>
                <select
                  v-model="quotePolicy"
                  id="policy"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="public">Public - Anyone can quote</option>
                  <option value="followers">Followers - Only followers can quote</option>
                  <option value="nobody">Nobody - Disable quoting</option>
                </select>
              </div>

              <button
                @click="enableQuotability"
                :disabled="loading || hasEnabledQuotability"
                class="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ loading ? 'Updating posts...' : hasEnabledQuotability ? 'Quotability Enabled' : 'Enable Quotability' }}
              </button>
            </div>

            <!-- Results -->
            <div v-if="results" class="bg-gray-50 rounded-lg p-4 mb-6">
              <h4 class="font-semibold text-gray-800 mb-2">Results</h4>
              <div class="space-y-1 text-sm">
                <div>Total posts: <span class="font-semibold">{{ results.total }}</span></div>
                <div class="text-green-600">Successfully updated: <span class="font-semibold">{{ results.success }}</span></div>
                <div v-if="results.failed > 0" class="text-red-600">Failed: <span class="font-semibold">{{ results.failed }}</span></div>
              </div>
              <p v-if="results.failed > 0" class="text-xs text-gray-500 mt-2">
                Note: Some posts may have failed due to visibility settings (private/direct posts cannot have their quote policy changed)
              </p>
            </div>

            <button
              @click="logout"
              class="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg font-medium hover:bg-gray-300 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <footer class="text-center mt-12 text-gray-600 text-sm">
        <p>
          This tool uses the Mastodon 4.5+ API to manage quote post settings.
        </p>
        <p class="mt-2">
          Your credentials are stored securely and only used for this session.
        </p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = 'http://localhost:5000/api'

// State
const step = ref('connect') // 'connect', 'authorize', 'account'
const instanceUrl = ref('')
const sessionId = ref(null)
const authUrl = ref('')
const authCode = ref('')
const accountInfo = ref(null)
const quotePolicy = ref('public')
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const hasEnabledQuotability = ref(false)
const results = ref(null)

// Clear messages after a timeout
const clearMessages = () => {
  setTimeout(() => {
    error.value = null
    success.value = null
  }, 5000)
}

// Start OAuth flow
const startAuth = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await fetch(`${API_BASE}/auth/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instance_url: instanceUrl.value })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || 'Failed to start authentication')
    }

    sessionId.value = data.session_id
    authUrl.value = data.auth_url
    step.value = 'authorize'

  } catch (err) {
    error.value = err.message
    clearMessages()
  } finally {
    loading.value = false
  }
}

// Complete OAuth flow
const completeAuth = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await fetch(`${API_BASE}/auth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        auth_code: authCode.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || 'Failed to complete authentication')
    }

    success.value = 'Successfully authenticated!'
    clearMessages()
    await loadAccountInfo()

  } catch (err) {
    error.value = err.message
    clearMessages()
  } finally {
    loading.value = false
  }
}

// Load account information
const loadAccountInfo = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await fetch(`${API_BASE}/account/info?session_id=${sessionId.value}`)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || 'Failed to load account info')
    }

    accountInfo.value = data
    step.value = 'account'

  } catch (err) {
    error.value = err.message
    clearMessages()
  } finally {
    loading.value = false
  }
}

// Enable quotability for all posts
const enableQuotability = async () => {
  if (hasEnabledQuotability.value) return

  if (!confirm(`This will update all ${accountInfo.value.posts_count} posts to allow quoting with policy "${quotePolicy.value}". Continue?`)) {
    return
  }

  try {
    loading.value = true
    error.value = null
    results.value = null

    const response = await fetch(`${API_BASE}/quotability/enable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        policy: quotePolicy.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || 'Failed to enable quotability')
    }

    results.value = data
    hasEnabledQuotability.value = true
    success.value = `Successfully updated ${data.success} posts!`
    clearMessages()

  } catch (err) {
    error.value = err.message
    clearMessages()
  } finally {
    loading.value = false
  }
}

// Logout
const logout = async () => {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId.value })
    })

    // Reset state
    step.value = 'connect'
    instanceUrl.value = ''
    sessionId.value = null
    authUrl.value = ''
    authCode.value = ''
    accountInfo.value = null
    hasEnabledQuotability.value = false
    results.value = null
    success.value = 'Logged out successfully'
    clearMessages()

  } catch (err) {
    error.value = 'Failed to logout: ' + err.message
    clearMessages()
  }
}
</script>
