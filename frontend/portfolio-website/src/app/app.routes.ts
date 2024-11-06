import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';
import { HistoryComponent } from './features/history/history.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'home', component: HomeComponent },
  { path: 'history', component: HistoryComponent },
  { path: '2024', component: HomeComponent },
  { path: 'utilities', component: HomeComponent },
  { path: '**', redirectTo: '' }
];
