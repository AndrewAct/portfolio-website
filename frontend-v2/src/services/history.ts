import type { AxiosInstance } from 'axios'
import axios from 'axios'

export interface MediumPost {
  title: string
  link: string
  author: string
  published_date: string
  content: string
  reading_time: number
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'https://andrewcee.io'

const http: AxiosInstance = axios.create({
  baseURL: `${apiBaseUrl}/api`
})

export async function getMediumPosts(username: string): Promise<MediumPost[]> {
  const { data } = await http.get<MediumPost[]>(`/medium-posts/${username}`)
  return data
}
