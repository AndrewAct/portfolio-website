export interface HoroscopeResponse {
  zodiac_sign: string;
  zodiac_sign_chinese?: string;
  daily_horoscope: string;
  lucky_number?: number;
  compatibility?: string;
  mood?: string;
}

export interface BirthdateRequest {
  birthdate: string;
  gender: string;
  language: string;
}

export interface ZodiacSign {
  englishName: string;
  localizedName: string;
  startDate: string;
  endDate: string;
}
