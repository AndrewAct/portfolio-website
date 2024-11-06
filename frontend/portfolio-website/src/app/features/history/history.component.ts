// src/app/features/history/history.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { MediumService } from './medium.service';
import { MediumPost } from './medium-post.interface';

@Component({
  selector: 'app-history',
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.scss'],
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  providers: [MediumService]  // Add this line to provide the service
})
export class HistoryComponent implements OnInit {
  mediumPosts: MediumPost[] = [];
  loading: boolean = false;
  error: string | null = null;
  readonly DEFAULT_USERNAME = 'andrewact';

  constructor(private mediumService: MediumService) {}

  ngOnInit() {
    this.loading = true;
    this.mediumService.getMediumPosts(this.DEFAULT_USERNAME)
      .subscribe({
        next: (posts) => {
          this.mediumPosts = posts;
          this.loading = false;
          this.error = null;
        },
        error: (error) => {
          console.error('Error fetching Medium posts:', error);
          this.error = 'Failed to load Medium posts. Please try again later.';
          this.loading = false;
        }
      });
  }

  getExcerpt(content: string): string {
    const plainText = content.replace(/<[^>]+>/g, '');
    return plainText.substring(0, 150) + '...';
  }
}
