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

// Use andrewcee.io domain for production, localhost for development
const baseUrl = import.meta.env.DEV ? 'http://localhost:8000/utilities/horoscope' : 'https://andrewcee.io/utilities/horoscope'

export async function getHoroscopeBySign(sign: string, gender: string, language = 'en') {
  const { data } = await axios.get<HoroscopeResponse>(`${baseUrl}/${sign}`, {
    params: { gender, language }
  })
  return data
}

export async function getHoroscopeByBirthdate(request: BirthdateRequest) {
  // console.log(request);
  // console.log(`The base URL is: ${baseUrl}`);
  const { data } = await axios.post<HoroscopeResponse>(`${baseUrl}`, request)
  return data
}
