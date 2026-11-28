import { useEffect, useLayoutEffect, useRef } from 'react'
import type { KeyboardEvent as ReactKeyboardEvent } from 'react'

export type MenuItem = {
  label: string
  onSelect: () => void
  danger?: boolean // shown in red, for things like Delete
}

type ContextMenuProps = {
  x: number // where the right-click happened, in window coordinates
  y: number
  items: MenuItem[]
  onClose: () => void
}

// A small menu that opens where the coach right-clicked, replacing the
// browser's own right-click menu.
function ContextMenu({ x, y, items, onClose }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)

  // Keep the menu on screen: near the right or bottom edge of the window, it
  // opens to the left or upward instead. useLayoutEffect runs after React adds
  // the menu to the page but before the browser draws it, so the menu can be
  // measured and moved without visibly jumping.
  useLayoutEffect(() => {
    const menu = menuRef.current
    if (menu === null) {
      return
    }
    const { width, height } = menu.getBoundingClientRect()
    menu.style.left = `${Math.min(x, window.innerWidth - width - 4)}px`
    menu.style.top = `${Math.min(y, window.innerHeight - height - 4)}px`
    // Focus the first item so the keyboard works right away
    menu.querySelector('button')?.focus()
  }, [x, y])

  // Close when the coach clicks anywhere else, presses Esc, scrolls, or
  // resizes the window. These listeners go on the whole document because those
  // events happen outside the menu, where React's onClick props can't see them.
  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        onClose()
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    // true = "capture": also catches scrolling inside the schedule or panel,
    // which doesn't bubble up to the document like other events do
    document.addEventListener('scroll', onClose, true)
    window.addEventListener('resize', onClose)

    // Remove them again when the menu closes, or they'd keep running forever
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('scroll', onClose, true)
      window.removeEventListener('resize', onClose)
    }
  }, [onClose])

  // Up and down arrows move between the items, like a real menu
  function handleMenuKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') {
      return
    }
    event.preventDefault()
    const buttons = [...event.currentTarget.querySelectorAll('button')]
    const current = buttons.indexOf(document.activeElement as HTMLButtonElement)
    const step = event.key === 'ArrowDown' ? 1 : -1
    buttons[(current + step + buttons.length) % buttons.length].focus()
  }

  return (
    <div
      ref={menuRef}
      className="context-menu"
      role="menu"
      style={{ left: x, top: y }}
      onKeyDown={handleMenuKeyDown}
      onContextMenu={(event) => event.preventDefault()}
    >
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          role="menuitem"
          className={item.danger ? 'context-menu-item danger' : 'context-menu-item'}
          onClick={() => {
            onClose()
            item.onSelect()
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}

export default ContextMenu
