/**
 * Layout configuration for horizontal tree layout (left to right)
 * Customize these values to adjust spacing and appearance
 */

export const LAYOUT_CONFIG = {
  // Horizontal spacing between levels (left to right)
  LEVEL_SPACING_X: 250,

  // Vertical spacing between siblings
  SPACING_Y: 90,

  // Starting position for the root node
  ROOT_X: -420,
  ROOT_Y: 0,
};

/**
 * Calculate vertical position for children based on index and count
 * This centers the children vertically around the parent
 */
export const calculateChildY = (
  index: number,
  totalChildren: number,
  spacingY: number
): number => {
  const totalHeight = (totalChildren - 1) * spacingY;
  const startY = -(totalHeight / 2);
  return startY + index * spacingY;
};

