/** Pita judul halaman (judul + keterangan + cap nomor). */
import React from "react";

export default function PageHeading({ section = "THE SCREENING ROOM", index = "01", title, description }) {
  return (
    <section className="page-heading">
      <div className="heading-copy">
        <div className="eyebrow">
          <span className="eyebrow-line" aria-hidden="true" />
          {section} <span className="eyebrow-dot">/</span> {index}
        </div>
        <h1>
          {title}
          <span className="title-period">.</span>
        </h1>
        {description ? <p>{description}</p> : null}
      </div>
      <div className="heading-stamp">
        <span>ISSUE</span>
        <strong>NO. 04</strong>
        <small>EST. 2026</small>
      </div>
    </section>
  );
}
