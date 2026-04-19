import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CinemaService } from '../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  cinema = inject(CinemaService);
  featured = toSignal(this.cinema.getFeaturedMovies(), { initialValue: [] });
  theaters = toSignal(this.cinema.getTheaters(), { initialValue: [] });
}