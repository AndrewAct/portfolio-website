import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { URLBase, URLResponse, DeleteURLRequest} from '../models/url.model';
import { environment } from '../../../../environments/environment'

@Injectable({
  providedIn: 'root'
})
export class UrlShortenerService {
  // private baseUrl = 'http://localhost:8000/utilities/url_shortener'; // Development mode
  private baseUrl = 'https://andrewcee.io/utilities/url_shortener'; // Production mode

  constructor(private http: HttpClient) {}

  createShortUrl(urlData: URLBase): Observable<URLResponse> {
    return this.http.post<URLResponse>(this.baseUrl, urlData);
  }

  getOriginalUrl(shortUrl: string): Observable<URLResponse> {
    return this.http.get<URLResponse>(`${this.baseUrl}/${shortUrl}`);
  }

  deleteUrl(shortUrl: string): Observable<void> {
    // Updated to send URL in request body
    return this.http.delete<void>(`${this.baseUrl}/`, {
      body: { url: shortUrl }
    });
  }

  getServiceInfo(): Observable<any> {
    return this.http.get(this.baseUrl);
  }
}
