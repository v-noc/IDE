import { createBrowserRouter } from "react-router-dom";

import { homeRoute } from "./Projects";

export const router = createBrowserRouter([
  {
    path: "/",

    children: [homeRoute],
  },
]);
