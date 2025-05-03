import { createBrowserRouter } from "react-router-dom";
import HomePage from "./App";
import ChatPage from "./components/ui/customs/chat";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/chat",
    element: <ChatPage />,
  },
]);
