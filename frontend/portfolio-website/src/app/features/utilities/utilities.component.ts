import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { UrlShortenerComponent } from '../url-shortener/url-shortener.component';
import { HoroscopeComponent } from '../horoscope/horoscope.component';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-utilities',
  standalone: true,
  imports: [CommonModule, UrlShortenerComponent, HoroscopeComponent, HttpClientModule],
  templateUrl: './utilities.component.html',
  styleUrl: './utilities.component.scss'
})
export class UtilitiesComponent {
  showUrlShortener = false;
  showHoroscope = false;

  constructor(private router: Router) {
    // By default, show horoscope when first loading the page
    this.showHoroscope = true;
  }

  onUrlShortenerClick(): void {
    this.showUrlShortener = true;
    this.showHoroscope = false;
  }

  onHoroscopeClick(): void {
    this.showHoroscope = true;
    this.showUrlShortener = false;
  }
}
