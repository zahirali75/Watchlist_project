/** Logo MovieWatchlist: ikon reel film (SVG) + nama produk dengan aksen emas. */
import React from "react";

export function ReelIcon({ size = 36, className = "" }) {
  const holes = [
    [18, 8.5],
    [27.5, 18],
    [18, 27.5],
    [8.5, 18],
    [18, 18],
  ];
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 36 36" aria-hidden="true" focusable="false">
      <circle cx="18" cy="18" r="17" fill="currentColor" />
      {holes.map(([cx, cy], index) => (
        <circle key={index} cx={cx} cy={cy} r={index === 4 ? 3.2 : 4.2} fill="var(--color-bg)" />
      ))}
    </svg>
  );
}

export default function Logo({ onClick }) {
  return (
    <button type="button" className="brand" onClick={onClick} aria-label="MovieWatchlist — Home">
      <ReelIcon size={34} className="brand-reel" />
      <span className="brand-name">
        Cine<span>List</span>
      </span>
    </button>
  );
}
