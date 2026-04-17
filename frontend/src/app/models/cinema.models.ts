export interface Theater {
  id: number;
  name: string;
  address: string;
  imageUrl?: string;
}

export interface Movie {
  id: number;
  title: string;
  synopsis: string;
  posterUrl: string;
  backdropUrl?: string;
  genre: string;
  duration: number; // minutes
  rating: string;   // e.g. "PG-13"
  featured?: boolean;
}

export interface Showing {
  id: number;
  movieId: number;
  theaterId: number;
  datetime: string; // ISO string
  purchaseUrl: string;
  format?: string;  // e.g. "IMAX", "4DX", "Standard"
}