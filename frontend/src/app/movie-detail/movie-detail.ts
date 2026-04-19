import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CinemaService } from '../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';

@Component({
  selector: 'app-movie-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './movie-detail.component.html',
  styleUrl: './movie-detail.component.scss',
})
export class MovieDetailComponent {
  private route = inject(ActivatedRoute);
  private cinema = inject(CinemaService);

  movie = toSignal(
    this.route.paramMap.pipe(
      switchMap(p => this.cinema.getMovie(Number(p.get('id'))))
    )
  );

  theaterShowings = toSignal(
    this.route.paramMap.pipe(
      switchMap(p => this.cinema.getShowingsForMovie(Number(p.get('id'))))
    ),
    { initialValue: [] }
  );

  formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatDate(iso: string) {
    return new Date(iso).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  }
}