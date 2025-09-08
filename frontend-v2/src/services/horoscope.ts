import axios from 'axios'

export interface HoroscopeResponse {
  zodiac_sign: string
  zodiac_sign_chinese?: string
  daily_horoscope: string
  lucky_number?: number
  compatibility?: string
  mood?: string
}

export interface BirthdateRequest {
  birthdate: string
  gender: string
  language: string
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'https://andrewcee.io'
const baseUrl = `${apiBase}/utilities/horoscope`

export async function getHoroscopeBySign(sign: string, gender: string, language = 'en') {
  const { data } = await axios.get<HoroscopeResponse>(`${baseUrl}/${sign}`, {
    params: { gender, language }
  })
  return data
}

export async function getHoroscopeByBirthdate(request: BirthdateRequest) {
  const { data } = await axios.post<HoroscopeResponse>(`${baseUrl}`, request)
  return data
}
