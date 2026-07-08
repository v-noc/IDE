const SENTENCES = [
  "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
  "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
  "Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
  "Duis aute irure dolor in reprehenderit in voluptate velit esse.",
  "Excepteur sint occaecat cupidatat non proident sunt in culpa.",
];

function pick<T>(items: T[], seed: number): T {
  return items[Math.abs(seed) % items.length];
}

export function loremIntro(nodeName: string, nodeType: string): string {
  const a = pick(SENTENCES, nodeName.length);
  const b = pick(SENTENCES, nodeName.charCodeAt(0) + nodeType.length);
  return `${a} This ${nodeType} "${nodeName}" is the focus here. ${b}`;
}

export function loremBlockText(focus: string, blockIndex: number): string {
  const a = pick(SENTENCES, focus.length + blockIndex);
  const b = pick(SENTENCES, focus.charCodeAt(0) + blockIndex * 3);
  const c = pick(SENTENCES, focus.length * 2 + blockIndex);
  return `${a} The "${focus}" section ${b} ${c}`;
}
