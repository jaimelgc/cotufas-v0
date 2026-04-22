import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CinemaService } from './cinema.service';
import { Movie, Theater } from '../models/cinema.models';
import { combineLatest, map, of, switchMap } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

export interface SearchResult {
  type: 'movie' | 'theater';
  id: number;
  label: string;
}

@Injectable({ providedIn: 'root' })
export class SearchService {
  private cinema = inject(CinemaService);
  private router = inject(Router);

  query = signal('');

  private query$ = new Subject<string>();

  results$ = this.query$.pipe(
    debounceTime(200),
    distinctUntilChanged(),
    switchMap(q => {
      if (!q.trim()) return of([]);
      return combineLatest([this.cinema.getMovies(), this.cinema.getTheaters()]).pipe(
        map(([movies, theaters]) => {
          const lower = q.toLowerCase();
          const movieResults: SearchResult[] = movies
            .filter(m => m.title.toLowerCase().includes(lower))
            .slice(0, 5)
            .map(m => ({ type: 'movie', id: m.id, label: m.title }));
          const theaterResults: SearchResult[] = theaters
            .filter(t => t.name.toLowerCase().includes(lower))
            .slice(0, 3)
            .map(t => ({ type: 'theater', id: t.id, label: t.name }));
          return [...movieResults, ...theaterResults];
        })
      );
    })
  );

  search(q: string) {
    this.query.set(q);
    this.query$.next(q);
  }

  navigate(result: SearchResult) {
    const path = result.type === 'movie'
      ? ['/movies', result]
      : ['/theaters', result];
    this.router.navigate(path);
    this.query.set('');
    this.query$.next('');
  }
}