import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CinemaService } from '../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';
import { formatShowtime, formatShowdate } from '../utils/date.utils';
import { computed, signal } from '@angular/core';

@Component({
  selector: 'app-movie-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './movie-detail.html',
  styleUrl: './movie-detail.scss',
})
export class MovieDetailComponent {
  private route = inject(ActivatedRoute);
  private cinema = inject(CinemaService);
  protected formatShowtime = formatShowtime;
  protected formatShowdate = formatShowdate;

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

  // explicit expand/collapse overrides per "theaterId::date", keyed so each
  // day gets its own independent toggle button instead of a single dropdown
  private expandedOverrides = signal<Map<string, boolean>>(new Map());

  // group each theater's showings by date
  theaterShowingsGrouped = computed(() => {
    return this.theaterShowings().map(ts => {
      const groups = new Map<string, typeof ts.showings>();
      for (const s of ts.showings) {
        if (!groups.has(s.date)) groups.set(s.date, []);
        groups.get(s.date)!.push(s);
      }
      const dates = Array.from(groups.keys()).sort(); // chronological
      return { theater: ts.theater, dates, groups };
    });
  });

  formatGenres(genres: string[]): string {
    return genres.join(", ")
  }

  private dateKey(theaterId: number, date: string): string {
    return `${theaterId}::${date}`;
  }

  // First date of each theater is expanded by default; every other date
  // starts collapsed until its own button is clicked.
  isExpanded(theaterId: number, date: string, index: number): boolean {
    const override = this.expandedOverrides().get(this.dateKey(theaterId, date));
    return override !== undefined ? override : index === 0;
  }

  toggleDate(theaterId: number, date: string, index: number) {
    const key = this.dateKey(theaterId, date);
    const current = this.isExpanded(theaterId, date, index);
    this.expandedOverrides.update(overrides => {
      const next = new Map(overrides);
      next.set(key, !current);
      return next;
    });
  }

  getShowingsForDate(tg: { dates: string[]; groups: Map<string, any[]> }, date: string) {
    return tg.groups.get(date) ?? [];
  }
}