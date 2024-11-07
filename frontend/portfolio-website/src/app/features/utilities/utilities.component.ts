import {Component, OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import {NavigationEnd, Router} from '@angular/router';

@Component({
  selector: 'app-utilities',
  standalone: true,
  imports: [],
  templateUrl: './utilities.component.html',
  styleUrl: './utilities.component.scss'
})
export class UtilitiesComponent {
  constructor(private router: Router) {
  }

  onUrlShortenerClick(): void {
    // TODO: Implement URL shortener functionality or navigation
    console.log('URL Shortener clicked');
    // Example: this.router.navigate(['/utilities/url-shortener']);
  }
}
