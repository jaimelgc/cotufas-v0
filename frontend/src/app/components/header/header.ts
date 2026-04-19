import { Component, inject, signal, HostListener, ElementRef } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SearchService, SearchResult } from '../../services/search.service';
import { CinemaService } from '../../services/cinema.service';
import { toSignal } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss',
})
export class HeaderComponent {
  private el = inject(ElementRef);
  search = inject(SearchService);
  cinema = inject(CinemaService);

  theaters = toSignal(this.cinema.getTheaters(), { initialValue: [] });
  results  = toSignal(this.search.results$, { initialValue: [] });
  open = signal(false);

  onInput(e: Event) {
    const q = (e.target as HTMLInputElement).value;
    this.search.search(q);
    this.open.set(q.length > 0);
  }

  pick(r: SearchResult) {
    this.search.navigate(r);
    this.open.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocClick(e: MouseEvent) {
    if (!this.el.nativeElement.contains(e.target)) this.open.set(false);
  }
}