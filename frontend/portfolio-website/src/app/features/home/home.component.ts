import {Component, OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import {NavigationEnd, Router} from '@angular/router';
import {filter} from 'rxjs/operators';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class HomeComponent {
  isHome = true;
  showFallback = false;
  imagePath = 'assets/images/homepage_image.jpg';

  constructor(private router: Router) {}

  ngOnInit() {
    // Existing router code...
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.isHome = event.urlAfterRedirects === '/' || event.urlAfterRedirects === '/home';
      }
    });

    // Log the full image path
    console.log('Attempting to load image from:', this.imagePath);
  }

  handleImageError(event: any) {
    console.error('Image failed to load:', event);
    this.showFallback = true;

    // Log the actual src attribute
    const img = event.target as HTMLImageElement;
    console.log('Failed image src:', img.src);
  }

  handleImageLoad(event: any) {
    console.log('Image loaded successfully');
    this.showFallback = false;
  }

  navigate(path: string) {
    const encodedPath = path.split('/')
    .map(segment => segment ? encodeURIComponent(segment) : '')
    .join('/');

    this.router.navigate([`/${encodedPath}`]);
  }
}


