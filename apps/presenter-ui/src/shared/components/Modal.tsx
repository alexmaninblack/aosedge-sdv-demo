import { useEffect, useId, useRef, type ReactNode } from "react";

// Nested record/confirmation dialogs handle keys independently of their parent.
const dialogStack: HTMLDivElement[] = [];

export interface ModalProps {
  title: string;
  subtitle: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  variant?: "studio";
  accent?: "brake" | "tire" | "platform";
}

export function Modal({ title, subtitle, onClose, children, footer, variant, accent }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  // Capture before the parent workspace becomes inert, including StrictMode's
  // mount/effect replay. Subsequent observation renders must not replace it.
  const returnFocus = useRef<HTMLElement | null>(document.activeElement instanceof HTMLElement ? document.activeElement : null);
  const close = useRef(onClose);
  close.current = onClose;
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const parent = dialogStack.at(-1);
    if (parent && !parent.contains(dialog)) parent.inert = true;
    dialogStack.push(dialog);
    dialog?.querySelector<HTMLElement>("button")?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (dialogStack.at(-1) !== dialog) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopImmediatePropagation();
        close.current();
        return;
      }
      if (event.key !== "Tab" || !dialog) return;
      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>("button,input,select,textarea,summary,[href],[tabindex]:not([tabindex='-1'])"))
        .filter(element => !element.matches(":disabled,[hidden]") && !element.closest("[inert]") && element.getClientRects().length > 0);
      if (!focusable.length) return;
      const first = focusable[0]!;
      const last = focusable.at(-1)!;
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      const index = dialogStack.indexOf(dialog);
      if (index >= 0) dialogStack.splice(index, 1);
      if (parent) parent.inert = false;
      if (!dialog.isConnected && returnFocus.current?.isConnected) returnFocus.current.focus();
    };
  }, []);

  return (
    <div className={`modal-layer${variant ? " studio-modal-layer" : ""}`} data-team={accent} role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && dialogStack.at(-1) === dialogRef.current) onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={titleId} ref={dialogRef} tabIndex={-1}>
        <header className="modal-head">
          <div>
            <h2 id={titleId}>{title}</h2>
            <p>{subtitle}</p>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close dialog">×</button>
        </header>
        <div className="modal-body">{children}</div>
        <footer className="modal-footer">{footer ?? <button className="button button-primary" onClick={onClose}>Close</button>}</footer>
      </div>
    </div>
  );
}
