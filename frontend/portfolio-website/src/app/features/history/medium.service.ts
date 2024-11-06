// src/app/features/history/medium.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MediumPost } from './medium-post.interface';

@Injectable({
  providedIn: 'root'
})
export class MediumService {
  private apiUrl = 'http://localhost:8000/api';  // Adjust to match your FastAPI URL

  constructor(private http: HttpClient) {}

  getMediumPosts(username: string): Observable<MediumPost[]> {
    return this.http.get<MediumPost[]>(`${this.apiUrl}/medium-posts/${username}`);
  }
}
