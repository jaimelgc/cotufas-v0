import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CinemaService } from '../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';
import { formatShowtime, formatShowdate } from '../utils/date.utils';

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

  formatGenres(genres: string[]): string {
    return genres.join(", ")
  }
}