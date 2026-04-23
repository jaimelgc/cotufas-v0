export interface Theater {
  id: number;
  name: string;
  slug: string;
  location: string;
  city: string;
  base_prices: Record<string, number>;
  website: string;
}

export interface Movie {
  id: number;
  title: string;
  slug: string;
  length: number;
  age: number;
  actors: string[];
  directors: string[];
  producers: string[];
  genres: string[];
  theaters: string[];
  synopsis: string;
  all_synopsis: Record<string, string>;
  all_urls: Record<string, string>;
  cover_url: string;
  created_at: string;
  updated_at: string;
  featured?: boolean;
}

export interface Showing {
  id: number;
  movie: number;
  theater: number;
  date: string;
  time: string;
  format: string;
  purchaseUrl?: string; //add to back
}