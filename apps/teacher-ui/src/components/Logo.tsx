import { BrandWordmark } from "../../../shared/BrandMark";

export function Logo({ height = 28, iconOnly = false }: { height?: number; iconOnly?: boolean }) {
  return <BrandWordmark size={height} iconOnly={iconOnly} />;
}

