/**
 * Kartu genre dari data nyata. Backend belum punya endpoint agregasi genre, jadi:
 *   1. ambil 100 judul rating tertinggi, hitung genre yang paling sering muncul;
 *   2. untuk tiap genre teratas, panggil GET /movies?genre=X&limit=1 — `total` dari
 *      respons adalah jumlah judul sebenarnya di database, dan film pertamanya
 *      (rating tertinggi) menyumbang poster sebagai artwork kartu.
 */
import { Compass, Drama, Film, Flame, Ghost, Heart, Laugh, Orbit, Rocket, Skull, Swords } from "lucide-react";

import { moviesApi } from "../api/index.js";
import { genreList } from "./format.js";

const ICONS = [
  [/action/i, Flame],
  [/adventure/i, Compass],
  [/drama/i, Drama],
  [/sci/i, Orbit],
  [/horror/i, Ghost],
  [/thriller|crime/i, Skull],
  [/comedy/i, Laugh],
  [/romance/i, Heart],
  [/fantasy|animation/i, Rocket],
  [/war|western/i, Swords],
];

export function genreIcon(name) {
  return ICONS.find(([pattern]) => pattern.test(name))?.[1] ?? Film;
}

export async function loadGenreCards(count, signal) {
  const { items } = await moviesApi.listMovies({ sort: "rating_desc", limit: 100, signal });
  const tally = new Map();
  for (const movie of items) {
    for (const name of genreList(movie.genre)) tally.set(name, (tally.get(name) || 0) + 1);
  }
  const names = [...tally.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, count)
    .map(([name]) => name);

  return Promise.all(
    names.map(async (name) => {
      const result = await moviesApi.listMovies({ genre: name, sort: "rating_desc", limit: 1, signal });
      return { name, total: result.total, poster: result.items[0]?.poster_url || "" };
    }),
  );
}
