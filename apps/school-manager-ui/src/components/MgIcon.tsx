import React from "react";
import { RolePortalIcon, RolePortalIconName } from "../../../shared/RoleDashboardIcon";

export type MgIconName = RolePortalIconName;

export function MgIcon({ name, size = 20, color = "currentColor" }: { name: MgIconName; size?: number; color?: string }) {
  return <RolePortalIcon name={name} size={size} color={color} />;
}