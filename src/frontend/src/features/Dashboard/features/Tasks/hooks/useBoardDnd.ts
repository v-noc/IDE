import { useCallback, useState } from "react";
import type { Task } from "@/types/tasks";

const RANK_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz";
const RANK_MIN = RANK_ALPHABET[0];
const RANK_MAX = RANK_ALPHABET[RANK_ALPHABET.length - 1];
const RANK_MID = RANK_ALPHABET[Math.floor(RANK_ALPHABET.length / 2)];

export function midRank(left: string | null, right: string | null): string {
  if (!left && !right) return RANK_MID;
  if (!left) left = RANK_MIN;
  if (!right) right = RANK_MAX;

  const result: string[] = [];
  let i = 0;
  while (true) {
    const leftChar = i < left.length ? left[i] : RANK_MIN;
    const rightChar = i < right.length ? right[i] : RANK_MAX;
    if (leftChar === rightChar) {
      result.push(leftChar);
      i += 1;
      if (i > Math.max(left.length, right.length) + 8) {
        return result.join("") + RANK_MID;
      }
      continue;
    }
    const leftIdx = RANK_ALPHABET.indexOf(leftChar);
    const rightIdx = RANK_ALPHABET.indexOf(rightChar);
    if (rightIdx - leftIdx > 1) {
      const midIdx = Math.floor((leftIdx + rightIdx) / 2);
      result.push(RANK_ALPHABET[midIdx]);
      return result.join("");
    }
    result.push(leftChar);
    i += 1;
  }
}

interface UseBoardDndOptions {
  tasks: Task[];
  onMove: (taskId: string, status: string, rank: string) => void;
}

export function useBoardDnd({ tasks, onMove }: UseBoardDndOptions) {
  const [draggingTaskId, setDraggingTaskId] = useState<string | null>(null);
  const [dropTargetColumnId, setDropTargetColumnId] = useState<string | null>(null);

  const handleDragStart = useCallback((taskId: string) => {
    setDraggingTaskId(taskId);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggingTaskId(null);
    setDropTargetColumnId(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDropTargetColumnId(columnId);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, columnId: string) => {
      e.preventDefault();
      const taskId = draggingTaskId;
      if (!taskId) return;

      const columnTasks = tasks
        .filter((t) => t.status === columnId && t.id !== taskId)
        .sort((a, b) => a.rank.localeCompare(b.rank));

      const rank = midRank(
        columnTasks.length > 0 ? columnTasks[columnTasks.length - 1].rank : null,
        null,
      );

      onMove(taskId, columnId, rank);
      setDraggingTaskId(null);
      setDropTargetColumnId(null);
    },
    [draggingTaskId, onMove, tasks],
  );

  return {
    draggingTaskId,
    dropTargetColumnId,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
  };
}
