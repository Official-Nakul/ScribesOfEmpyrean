import "./App.css";
import { BackgroundLines } from "./components/ui/background-lines";
import { AuroraBackground } from "./components/ui/aurora-background.tsx";
import { Routes, Route, useNavigate } from "react-router-dom";
import ChatPage from "./components/ui/customs/chat";

export function HomePage() {
  const navigate = useNavigate();

  return (
    <AuroraBackground
      children={
        <div className="flex flex-col justify-center items-center lexend px-4 md:px-8 z-10">
          <h1 className="text-white text-4xl md:text-6xl lg:text-7xl text-center">
            What if books could talk?
          </h1>
          <h1 className="text-gray-200 text-xl md:text-2xl lg:text-3xl mt-4 text-center">
            Explore the world of Empyrean through AI.
          </h1>
          <button
            onClick={() => navigate("/chat")}
            className="mt-8 bg-white/10 hover:bg-white/20 text-white font-medium py-3 px-6 rounded-lg transition-all duration-300 text-lg md:text-xl"
          >
            let's chat
          </button>
        </div>
      }
      className={
        "text-white text-4xl md:text-6xl lg:text-7xl justify-center items-center flex"
      }
    />
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/chat" element={<ChatPage />} />
    </Routes>
  );
}

export default App;
