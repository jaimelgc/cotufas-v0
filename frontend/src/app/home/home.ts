import { Component, signal } from '@angular/core';
import { MovieItem } from '../components/movie-item/movie-item';

@Component({
  selector: 'app-home',
  imports: [MovieItem],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home {
  title = signal('ese')
}
