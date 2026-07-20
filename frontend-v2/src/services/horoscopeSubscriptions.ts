import axios from 'axios'

export interface SubscriptionPreferences {
  email: string
  birthdate: string
  gender: string
  language: string
  timezone: string
  send_time_local: string
}

export interface SubscribeResponse {
  status: 'confirmation_sent'
}

export interface ConfirmResponse {
  status: 'confirmed' | 'already_confirmed'
}

export interface UpdatePreferencesResponse {
  status: 'updated' | 'confirmation_sent'
}

export interface UnsubscribeResponse {
  status: 'unsubscribed' | 'already_unsubscribed'
}

// Use andrewcee.io domain for production, localhost for development
const baseUrl = import.meta.env.DEV
  ? 'http://localhost:8000/utilities/horoscope/subscriptions'
  : 'https://andrewcee.io/utilities/horoscope/subscriptions'

export async function subscribe(preferences: SubscriptionPreferences) {
  const { data } = await axios.post<SubscribeResponse>(baseUrl, preferences)
  return data
}

export async function confirmSubscription(token: string) {
  const { data } = await axios.get<ConfirmResponse>(`${baseUrl}/confirm`, { params: { token } })
  return data
}

export async function getPreferences(token: string) {
  const { data } = await axios.get<SubscriptionPreferences>(`${baseUrl}/preferences`, {
    params: { token }
  })
  return data
}

export async function updatePreferences(token: string, preferences: SubscriptionPreferences) {
  const { data } = await axios.post<UpdatePreferencesResponse>(
    `${baseUrl}/preferences`,
    preferences,
    { params: { token } }
  )
  return data
}

export async function unsubscribe(token: string) {
  const { data } = await axios.post<UnsubscribeResponse>(`${baseUrl}/unsubscribe`, null, {
    params: { token }
  })
  return data
}

/** Extracts a FastAPI HTTPException's `detail` message, falling back for network/unknown errors. */
export function extractErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}
