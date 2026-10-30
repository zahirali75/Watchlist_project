/** Judul halaman (judul + keterangan). `section`/`index` dipertahankan agar pemanggil lama tidak rusak. */
import React from "react";

export default function PageHeading({ title, description }) {
  return (
    <section className="page-heading">
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </section>
  );
}
