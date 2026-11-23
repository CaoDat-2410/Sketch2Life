export interface NotificationText {
  title: string;
  body?: string;
}

const templates: ReadonlyMap<string, NotificationText> = new Map();

export function resolveNotificationText(type: string, templateVersion: number): NotificationText {
  const key = `${type}:${templateVersion}`;
  // A future notification type needs its own display text sourced from the SRS.
  return templates.get(key) ?? { title: "Thông báo mới" };
}
