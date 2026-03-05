
export const truncatePath = (path: string, maxLength = 50) => {
  if (path.length <= maxLength) return path
  return `...${path.slice(-(maxLength - 3))}`
}

export const idPrefixRemover = (id: string) => {
  return id.split("/").pop() as string;
}
