export interface ViewportState {
  x: number;
  y: number;
  zoom: number;
}

export interface CanvasSize {
  width: number;
  height: number;
}

export interface FlowNodeRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** True when the node's screen rect fits inside the canvas with margin. */
export function isNodeFullyInViewport(
  viewport: ViewportState,
  canvas: CanvasSize,
  node: FlowNodeRect,
  margin = 48,
): boolean {
  const { x, y, zoom } = viewport;
  const screenLeft = node.x * zoom + x;
  const screenTop = node.y * zoom + y;
  const screenRight = (node.x + node.width) * zoom + x;
  const screenBottom = (node.y + node.height) * zoom + y;

  return (
    screenLeft >= margin &&
    screenTop >= margin &&
    screenRight <= canvas.width - margin &&
    screenBottom <= canvas.height - margin
  );
}
