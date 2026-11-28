import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

type ModalProps = {
  title: string
  onClose: () => void
  children: ReactNode // whatever is written between <Modal> and </Modal>
}

// A pop-up built on the browser's own <dialog> element. Opening it with
// showModal() gives us the dimmed backdrop, keeps keyboard focus inside the
// dialog, and closes it on Esc, all without writing that code ourselves.
//
// The parent shows a Modal by rendering it and hides it by not rendering it,
// so "open" just means "on the page".
function Modal({ title, onClose, children }: ModalProps) {
  // useRef gives us the real <dialog> element React creates, so we can call
  // its showModal() method. (React has no prop for "open as a modal".)
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    // The `open` check matters in development: StrictMode runs effects twice,
    // and calling showModal() on a dialog that's already open throws an error.
    if (dialog !== null && !dialog.open) {
      dialog.showModal()
      // showModal() moves keyboard focus to the first thing it can focus, which
      // is the × button. Move it to the first form field instead, so the coach
      // can start typing straight away.
      dialog.querySelector<HTMLElement>('input, select, textarea')?.focus()
    }
  }, [])

  return (
    // onClose fires when the browser closes the dialog itself, e.g. on Esc
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-header">
        <h2>{title}</h2>
        <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      {children}
    </dialog>
  )
}

export default Modal
