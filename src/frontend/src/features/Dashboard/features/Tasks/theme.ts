export const TASK_TYPE_COLORS = {
  bug: "#e07a7a",
  improvement: "#4ecdc4",
  epic: "#a78bfa",
  task: "#9ba1ab",
} as const;

export const TYPES = {
  bug: { color: "#e07a7a", bg: "rgba(224,108,108,.09)", border: "rgba(224,108,108,.28)" },
  improvement: { color: "#4ecdc4", bg: "rgba(78,205,196,.09)", border: "rgba(78,205,196,.28)" },
  epic: { color: "#a78bfa", bg: "rgba(167,139,250,.09)", border: "rgba(167,139,250,.28)" },
  task: { color: "#9ba1ab", bg: "#22252b", border: "#2c2f36" },
} as const;

export const SURFACE = {
  panel: "#141518",
  input: "#15161a",
  chip: "#22252b",
  hover: "#17191d",
} as const;

export const BORDER = {
  panel: "#22252b",
  row: "#1e2026",
  input: "#26292f",
  chip: "#2c2f36",
  strong: "#33373f",
} as const;

export const TEXT = {
  bright: "#f0f2f5",
  heading: "#dfe2e7",
  body: "#c3c8d1",
  muted: "#9ba1ab",
  dim: "#8b919d",
  faint: "#5c6270",
  label: "#6b7280",
} as const;

export const GREEN = {
  core: "#3ecf72",
  btn: "#2c9a58",
  btnBorder: "#2f9d5c",
  link: "#61c98a",
  linkHover: "#7fdba3",
} as const;

export const AMBER = {
  core: "#e2a03f",
  text: "#e2b95a",
  bg: "rgba(226,160,63,.1)",
  border: "rgba(226,160,63,.4)",
  rowBg: "rgba(226,160,63,.04)",
} as const;

export const KIND_ICON: Record<string, { glyph: string; color: string }> = {
  function: { glyph: "ƒ", color: "#3ecf72" },
  class: { glyph: "◇", color: "#6b93c4" },
  file: { glyph: "≣", color: "#9ba1ab" },
  folder: { glyph: "▸", color: "#8b919d" },
  call: { glyph: "↦", color: "#8b919d" },
};

export const PRIORITY_COLORS = {
  none: "#6b7280",
  low: "#6b93c4",
  medium: "#e2c95a",
  high: "#e29a5a",
  urgent: "#ef6b6b",
} as const;

export const HOT_AMBER = AMBER.core;
export const HOT_AMBER_BG = AMBER.bg;
export const ANCHOR_GREEN = "#8fd4a8";
export const ANCHOR_GREEN_BG = "rgba(62,207,114,.07)";
