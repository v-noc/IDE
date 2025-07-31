import { createBrowserRouter } from "react-router-dom";

import { homeRoute } from "./HomePage";
import { dashboardRoute } from "./Dashboard";

export const router = createBrowserRouter([
  {
    path: "/",

    children: [homeRoute, dashboardRoute],
  },
]);
