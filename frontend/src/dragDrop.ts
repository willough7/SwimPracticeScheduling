import type { DragEvent } from 'react'

// Shared helpers for dragging swimmers between the bottom panel and the lanes.
//
// The browser's built-in drag and drop carries data in event.dataTransfer, tagged
// with a type. Using our own type name (instead of plain text) means the lanes
// only react to swimmers being dragged, not to text or files dragged in from
// elsewhere.
const SWIMMER_TYPE = 'application/x-swimmer-id'

export function startSwimmerDrag(event: DragEvent, swimmerId: number) {
  event.dataTransfer.setData(SWIMMER_TYPE, String(swimmerId))
  event.dataTransfer.effectAllowed = 'move'
}

// During a drag the browser only lets us check the data's *type*, not read it
// (so pages can't spy on what's being dragged over them). Reading it is only
// allowed on drop.
export function isSwimmerDrag(event: DragEvent): boolean {
  return event.dataTransfer.types.includes(SWIMMER_TYPE)
}

export function droppedSwimmerId(event: DragEvent): number | null {
  const value = event.dataTransfer.getData(SWIMMER_TYPE)
  return value === '' ? null : Number(value)
}
