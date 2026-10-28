/** Poster film dengan fallback teks bila `poster_url` kosong atau gagal dimuat. */
import React, { useState } from "react";
import { Film, Tv } from "lucide-react";

import { MEDIA_TYPE } from "../../lib/mediaType.js";
import { formatYear } from "../../lib/format.js";

export default function Poster({ item, className = "" }) {
  const [failed, setFailed] = useState(false);
  const posterUrl = item?.poster_url;
  const showImage = posterUrl && !failed;

  return showImage ? (
    <img
      src={posterUrl}
      alt={`Poster ${item.title}`}
      loading="lazy"
      className={className}
      onError={() => setFailed(true)}
    />
  ) : (
    <div className={`poster-fallback ${className}`.trim()}>
      <span aria-hidden="true">{item?.media_type === MEDIA_TYPE.series ? <Tv size={34} /> : <Film size={34} />}</span>
      <b>{item?.title || "Tanpa judul"}</b>
      <small>{formatYear(item?.release_year)}</small>
    </div>
  );
}
