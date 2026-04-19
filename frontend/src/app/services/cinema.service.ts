import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin, map } from 'rxjs';
import { Movie, Theater, Showing } from '../models/cinema.models';

@Injectable({ providedIn: 'root' })
export class CinemaService {
  private http = inject(HttpClient);
  private base = 'http://127.0.0.1:8000/api';

  getTheaters(): Observable<Theater[]> {
    return this.http.get<Theater[]>(`${this.base}/theaters`);
  }

  getTheater(id: number): Observable<Theater> {
    return this.http.get<Theater>(`${this.base}/theaters/${id}`);
  }

  getMovies(): Observable<Movie[]> {
    return this.http.get<Movie[]>(`${this.base}/movies`);
  }

  getFeaturedMovies(): Observable<Movie[]> {
    return this.http.get<Movie[]>(`${this.base}/movies`).pipe(
      map(movies => movies.filter(m => m.featured).slice(0, 4))
    );
  }

  getMovie(id: number): Observable<Movie> {
    return this.http.get<Movie>(`${this.base}/movies/${id}`);
  }

  getShowings(filters: { movieId?: number; theaterId?: number } = {}): Observable<Showing[]> {
    const params: any = {};
    if (filters.movieId)   params['movieId']   = filters.movieId;
    if (filters.theaterId) params['theaterId'] = filters.theaterId;
    return this.http.get<Showing[]>(`${this.base}/showings`, { params });
  }

  // Utility: showings for a movie grouped by theater
  getShowingsForMovie(movieId: number): Observable<{ theater: Theater; showings: Showing[] }[]> {
    return forkJoin({
      theaters: this.getTheaters(),
      showings: this.getShowings({ movieId }),
    }).pipe(
      map(({ theaters, showings }) =>
        theaters.map(theater => ({
          theater,
          showings: showings
            .filter(s => s.theater === theater.id)
            .sort((a, b) => new Date(a.datetime).getTime() - new Date(b.datetime).getTime()),
        }))
      )
    );
  }
}