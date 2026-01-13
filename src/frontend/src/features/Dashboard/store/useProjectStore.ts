import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import { createSelectionSlice, type SelectionSlice } from './slices/selectionSlice';
import { createFocusSlice, type FocusSlice } from './slices/focusSlice';
import { createUISlice, type UISlice } from './slices/uiSlice';
import { createDataSlice, type DataSlice } from './slices/dataSlice';

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

const useProjectStore = create<ProjectStore>()(
  devtools(
    immer((...a) => ({
      ...createSelectionSlice(...a),
      ...createFocusSlice(...a),
      ...createUISlice(...a),
      ...createDataSlice(...a),
    })),
    { name: 'project-store' }
  )
);

export default useProjectStore;
