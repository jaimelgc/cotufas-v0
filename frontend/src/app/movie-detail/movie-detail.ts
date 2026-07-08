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

  // selected date per theater, keyed by theater id
  selectedDates = signal<Record<number, string>>({});

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

  getSelectedDate(theaterId: number, dates: string[]): string {
    return this.selectedDates()[theaterId] ?? dates[0];
  }

  onDateChange(theaterId: number, date: string) {
    this.selectedDates.update(m => ({ ...m, [theaterId]: date }));
  }

  getShowingsForDate(tg: { theater: any; dates: string[]; groups: Map<string, any[]> }) {
    const date = this.getSelectedDate(tg.theater.id, tg.dates);
    return tg.groups.get(date) ?? [];
  }
}