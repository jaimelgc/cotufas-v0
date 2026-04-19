import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', loadComponent: () => import('./home/home').then(m => m.HomeComponent) },
  { path: 'theaters/:id', loadComponent: () => import('./theater-detail/theater-detail').then(m => m.TheaterDetailComponent) },
  { path: 'movies/:id', loadComponent: () => import('./movie-detail/movie-detail').then(m => m.MovieDetailComponent) },
];