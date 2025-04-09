import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { HoroscopeResponse, BirthdateRequest } from '../models/horoscope.model';

@Injectable({
  providedIn: 'root'
})
export class HoroscopeService {
  // private baseUrl = 'http://localhost:8000/utilities/horoscope'; // Development mode
  private baseUrl = 'https://andrewcee.io/utilities/horoscope/'; // Production mode

  constructor(private http: HttpClient) { }

  /**
   * Get horoscope by zodiac sign
   */
  getHoroscopeBySign(sign: string, gender: string, language: string = 'en'): Observable<HoroscopeResponse> {
    return this.http.get<HoroscopeResponse>(`${this.baseUrl}/${sign}?gender=${gender}&language=${language}`);
  }

  /**
   * Get horoscope by birthdate
   */
  getHoroscopeByBirthdate(request: BirthdateRequest): Observable<HoroscopeResponse> {
    return this.http.post<HoroscopeResponse>(`${this.baseUrl}`, request);
  }
}
