import React from "react";
import { ArrowLeft, CircleAlert, ExternalLink, LockKeyhole } from "lucide-react";
import { Link } from "react-router-dom";

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="s2l-page-heading">
      <div>
        <p className="s2l-page-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="s2l-page-lede">{description}</p>
      </div>
      {action && <div className="s2l-page-heading-action">{action}</div>}
    </header>
  );
}

export function FeatureAvailability({
  title,
  summary,
  requirement,
  dependencies,
  permissionNote,
  backTo,
  backLabel = "Quay lại tổng quan",
}: {
  title: string;
  summary: string;
  requirement: string;
  dependencies: string[];
  permissionNote?: string;
  backTo?: string;
  backLabel?: string;
}) {
  return (
    <section className="s2l-availability-card" aria-labelledby="availability-title">
      <div className="s2l-availability-heading">
        <span className="s2l-availability-icon" aria-hidden="true"><CircleAlert size={21} /></span>
        <div><span className="s2l-availability-status">Chưa khả dụng</span><h2 id="availability-title">{title}</h2></div>
      </div>
      <p className="s2l-availability-summary">{summary}</p>
      <div className="s2l-availability-requirement"><strong>Yêu cầu SRS</strong><p>{requirement}</p></div>
      {permissionNote && <div className="s2l-availability-permission"><LockKeyhole size={17} aria-hidden="true" /><p>{permissionNote}</p></div>}
      <div className="s2l-availability-dependencies">
        <h3>Đang thiếu</h3>
        <ul>{dependencies.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      {backTo && <Link className="s2l-secondary-link" to={backTo}><ArrowLeft size={16} aria-hidden="true" />{backLabel}</Link>}
    </section>
  );
}

export function SourceScopeNote({ children }: { children: React.ReactNode }) {
  return <p className="s2l-source-scope"><ExternalLink size={15} aria-hidden="true" />{children}</p>;
}