
export const truncatePath = (path: string, maxLength = 50) => {
    if (path.length <= maxLength) return path
    return `...${path.slice(-(maxLength - 3))}`
}