import { createBrowserRouter } from "react-router-dom";
import Layout from "@/components/Layout";
import { homeRoute } from "./home";
import { aboutRoute } from "./about";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [homeRoute, aboutRoute],
  },
]);
