import axios from 'axios'

export interface URLBase { url: string }
export interface URLResponse {
  original_url: string
  shortened_url: string
  created_at: string
}

// Use HTTP for local development, HTTPS for production
const apiBase = import.meta.env.VITE_API_BASE_URL ?? 
  (import.meta.env.DEV ? 'http://localhost:8000' : 'https://andrewcee.io')
const baseUrl = `${apiBase}/utilities/url_shortener`

export async function createShortUrl(body: URLBase) {
  const { data } = await axios.post<URLResponse>(baseUrl, body)
  return data
}

export async function getOriginalUrl(short: string) {
  const { data } = await axios.get<URLResponse>(`${baseUrl}/${short}`)
  return data
}

export async function deleteUrl(shortUrl: string) {
  await axios.delete(`${baseUrl}/`, { data: { url: shortUrl } })
}

export async function getServiceInfo() {
  const { data } = await axios.get(baseUrl)
  return data
}
