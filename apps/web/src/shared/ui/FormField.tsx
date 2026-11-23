import { Children, cloneElement, isValidElement, useId, type ReactElement, type ReactNode } from "react";
import { cn } from "./cn";

export type FormFieldProps = {
  label: ReactNode;
  id?: string;
  htmlFor?: string;
  required?: boolean;
  help?: ReactNode;
  error?: ReactNode;
  labelAction?: ReactNode;
  className?: string;
  children: ReactNode;
};

type ControlProps = {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
  "aria-required"?: boolean;
  children?: ReactNode;
};

function mergeDescribedBy(existing: string | undefined, added: string | undefined): string | undefined {
  if (!added) return existing;
  if (!existing) return added;
  const tokens = new Set([...existing.split(/\s+/), ...added.split(/\s+/)].filter(Boolean));
  return Array.from(tokens).join(" ") || undefined;
}

function isDirectControl(element: ReactElement): boolean {
  if (typeof element.type === "string") {
    return element.type === "input" || element.type === "textarea" || element.type === "select";
  }
  return true;
}

function wireFirstControl(
  nodes: ReactNode,
  controlId: string,
  describedBy: string | undefined,
  required: boolean | undefined,
  hasError: boolean,
): { nodes: ReactNode; wired: boolean } {
  const childArray = Children.toArray(nodes);
  const nextChildren: ReactNode[] = [];
  let wired = false;

  for (const child of childArray) {
    if (wired) {
      nextChildren.push(child);
      continue;
    }
    const result = wireControl(child, controlId, describedBy, required, hasError);
    if (result.wired) {
      wired = true;
    }
    nextChildren.push(result.node);
  }

  return { nodes: nextChildren, wired };
}

function wireControl(
  node: ReactNode,
  controlId: string,
  describedBy: string | undefined,
  required: boolean | undefined,
  hasError: boolean,
): { node: ReactNode; wired: boolean } {
  if (!isValidElement<ControlProps>(node)) return { node, wired: false };

  if (isDirectControl(node)) {
    const nextProps: Partial<ControlProps> = {};
    if (!node.props.id) nextProps.id = controlId;
    const mergedDescribedBy = mergeDescribedBy(node.props["aria-describedby"], describedBy);
    if (mergedDescribedBy !== undefined) nextProps["aria-describedby"] = mergedDescribedBy;
    if (required) nextProps["aria-required"] = true;
    if (hasError) nextProps["aria-invalid"] = true;
    return { node: cloneElement(node, nextProps), wired: true };
  }

  const inner = wireFirstControl(node.props.children, controlId, describedBy, required, hasError);
  if (!inner.wired) return { node, wired: false };
  return { node: cloneElement(node, undefined, inner.nodes), wired: true };
}

/** Shared accessible form field wrapper with label wiring, required marker, help text, and inline error. */
export function FormField({
  label,
  id,
  htmlFor,
  required,
  help,
  error,
  labelAction,
  className,
  children,
}: FormFieldProps) {
  const generatedId = useId();
  const controlId = htmlFor ?? id ?? generatedId;
  const helpId = help ? `${controlId}-help` : undefined;
  const errorId = error ? `${controlId}-error` : undefined;
  const describedBy = [errorId, helpId].filter(Boolean).join(" ") || undefined;
  const hasError = Boolean(error);

  const { nodes: wiredChildren } = wireFirstControl(children, controlId, describedBy, required, hasError);

  const labelNode = (
    <span className="cozy-form-label-group">
      <label htmlFor={controlId} className="cozy-form-label">
        {label}
      </label>
      {required && (
        <span className="cozy-form-required" aria-hidden="true">
          *
        </span>
      )}
    </span>
  );

  return (
    <div className={cn("cozy-form-field", className)}>
      {labelAction ? (
        <div className="cozy-form-field-header">
          {labelNode}
          {labelAction}
        </div>
      ) : (
        labelNode
      )}
      {wiredChildren}
      {help && (
        <p id={helpId} className="cozy-form-hint">
          {help}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="cozy-form-error">
          {error}
        </p>
      )}
    </div>
  );
}
