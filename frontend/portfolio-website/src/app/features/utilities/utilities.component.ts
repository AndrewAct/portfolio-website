import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { UrlShortenerComponent } from '../url-shortener/url-shortener.component';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-utilities',
  standalone: true,
  imports: [CommonModule, UrlShortenerComponent, HttpClientModule],
  templateUrl: './utilities.component.html',
  styleUrl: './utilities.component.scss'
})
export class UtilitiesComponent {
  showUrlShortener = false;

  constructor(private router: Router) {}

  onUrlShortenerClick(): void {
    this.showUrlShortener = !this.showUrlShortener;
  }
}
