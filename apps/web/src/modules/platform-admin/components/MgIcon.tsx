import { RolePortalIcon, type RolePortalIconName, type RoleDashboardIconVariant } from "../../../shared/RoleDashboardIcon";

export type MgIconName = RolePortalIconName;

export function MgIcon({ name, size = 20, color = "currentColor", variant = "standard" }: {
  name: MgIconName;
  size?: number;
  color?: string;
  variant?: RoleDashboardIconVariant;
}) {
  return <RolePortalIcon name={name} size={size} color={color} variant={variant} />;
}
