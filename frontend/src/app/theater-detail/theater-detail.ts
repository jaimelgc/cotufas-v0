import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CinemaService } from '../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';

@Component({
  selector: 'app-theater-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './theater-detail.component.html',
  styleUrl: './theater-detail.component.scss',
})
export class TheaterDetailComponent {
  private route = inject(ActivatedRoute);
  private cinema = inject(CinemaService);

  private id$ = this.route.paramMap.pipe(
    switchMap(p => [Number(p.get('id'))])
  );

  theater = toSignal(
    this.route.paramMap.pipe(
      switchMap(p => this.cinema.getTheater(Number(p.get('id'))))
    )
  );

  showings = toSignal(
    this.route.paramMap.pipe(
      switchMap(p => this.cinema.getShowings({ theaterId: Number(p.get('id')) }))
    ),
    { initialValue: [] }
  );

  movies = toSignal(this.cinema.getMovies(), { initialValue: [] });

  // Group showings by movie
  movieShowings = computed(() => {
    const showingMap = new Map<number, typeof this.showings()[0][]>();
    for (const s of this.showings()) {
      if (!showingMap.has(s.movie)) showingMap.set(s.movie, []);
      showingMap.get(s.movie)!.push(s);
    }
    return this.movies()
      .filter(m => showingMap.has(m.id))
      .map(m => ({ movie: m, showings: showingMap.get(m.id)! }));
  });

  formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatDate(iso: string) {
    return new Date(iso).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  }
}