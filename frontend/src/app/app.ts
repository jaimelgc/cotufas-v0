import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Home } from './home/home';
import { Header } from './components/header/header';
import { MovieItem } from './components/movie-item/movie-item';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Home, Header, MovieItem],
  template: `
    <app-header></app-header>
    <app-home></app-home>
  `,
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('frontend');
}
