// src/app/features/history/medium.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MediumPost } from './medium-post.interface';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class MediumService {
  // private apiUrl = 'http://localhost:8000/api';  // Adjust to match your FastAPI URL, development mode
  private apiUrl = 'https://andrewcee.io/api'; // Adjust to match your FastAPI URL, production mode

  constructor(private http: HttpClient) {
    // Debug log to verify which environment is being used
    console.log('Environment:', environment.production ? 'Production' : 'Development');
    console.log('API URL:', this.apiUrl);
  }

  getMediumPosts(username: string): Observable<MediumPost[]> {
    return this.http.get<MediumPost[]>(`${this.apiUrl}/medium-posts/${username}`);
  }
}
