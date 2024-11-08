import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UrlShortenerService } from './services/url-shortener.service';
import { URLResponse, DeleteURLRequest } from './models/url.model';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-url-shortener',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './url-shortener.component.html',
  styleUrls: ['./url-shortener.component.scss']
})
export class UrlShortenerComponent implements OnInit {
  urlInput = '';
  shortenedUrl = '';
  error = '';
  recentUrls: URLResponse[] = [];
  // saveHistory = false; // Default not to save recent URLs for users

  constructor(private urlShortenerService: UrlShortenerService) {}

  ngOnInit(): void {
    // Load history only when user selected
    // if (this.saveHistory) {
    //   const savedUrls = localStorage.getItem('recentUrls');
    //   if (savedUrls) {
    //     this.recentUrls = JSON.parse(savedUrls);
    //   }
    // }
    const savedUrls = sessionStorage.getItem('recentUrls');
    if (savedUrls) {
      this.recentUrls = JSON.parse(savedUrls);
    }
  }

  shortenUrl(): void {
    if (!this.urlInput) return;

    this.error = '';
    this.urlShortenerService.createShortUrl({ url: this.urlInput })
      .subscribe({
        next: (response) => {
          this.shortenedUrl = response.shortened_url;
          this.recentUrls.unshift(response);
          this.saveRecentUrls();
          this.urlInput = '';
        },
        error: (error) => {
          this.error = 'Failed to shorten URL. Please try again.';
          console.error('Error shortening URL:', error);
        }
      });
  }

  // deleteUrl(url: URLResponse): void {
  //   const shortUrl = url.shortened_url.split('/').pop();
  //   if (!shortUrl) return;
  //
  //   // this.urlShortenerService.deleteUrl(shortUrl)
  //   this.urlShortenerService.deleteUrl({url: this.shortenedUrl})
  //     .subscribe({
  //       next: () => {
  //         this.recentUrls = this.recentUrls.filter(u => u.shortened_url !== url.shortened_url);
  //         this.saveRecentUrls();
  //       },
  //       error: (error) => {
  //         this.error = 'Failed to delete URL. Please try again.';
  //         console.error('Error deleting URL:', error);
  //       }
  //     });
  // }

  deleteUrl(url: URLResponse): void {
    // No need to extract code from URL anymore
    console.log("URL to delete: ", url.shortened_url);
    this.urlShortenerService.deleteUrl(url.shortened_url)
      .subscribe({
        next: () => {
          this.recentUrls = this.recentUrls.filter(u => u.shortened_url !== url.shortened_url);
          this.saveRecentUrls();
        },
        error: (error) => {
          console.error('Error deleting URL:', error);
          this.error = 'Failed to delete URL. Please try again.';
        }
      });
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('URL copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy URL:', err);
      });
  }

  // private saveRecentUrls(): void {
  //   if (this.saveHistory) {
  //     localStorage.setItem('recentUrls', JSON.stringify(this.recentUrls.slice(0, 10)));
  //   }
  // }

  private saveRecentUrls(): void {
    sessionStorage.setItem('recentUrls', JSON.stringify(this.recentUrls.slice(0, 10)));
  }
  clearHistory(): void {
    localStorage.removeItem('recentUrls');
    this.recentUrls = [];
  }
}
