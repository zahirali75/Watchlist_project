/**
 * Kolom pencarian header. Mengirim kata kunci ke induk (→ GET /movies?search=...)
 * saat Enter ditekan; hasil, loading, kosong, dan error ditampilkan halaman Movies.
 * Backend hanya mencari berdasarkan judul, jadi placeholder tidak menjanjikan aktor.
 */
import React, { useEffect, useState } from "react";
import { Search, X } from "lucide-react";

export default function SearchBar({ query = "", onSearch, className = "", autoFocus = false }) {
  const [value, setValue] = useState(query);

  // Ikut berubah bila pencarian dibersihkan dari halaman lain.
  useEffect(() => setValue(query), [query]);

  function submit(event) {
    event.preventDefault();
    onSearch(value.trim());
  }

  function clear() {
    setValue("");
    onSearch("");
  }

  return (
    <form className={`search-bar ${className}`.trim()} role="search" onSubmit={submit}>
      <Search size={17} aria-hidden="true" />
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Search movies by title…"
        aria-label="Search movies by title"
        autoFocus={autoFocus}
      />
      {value ? (
        <button type="button" className="search-clear" onClick={clear} aria-label="Clear search">
          <X size={15} aria-hidden="true" />
        </button>
      ) : null}
    </form>
  );
}
