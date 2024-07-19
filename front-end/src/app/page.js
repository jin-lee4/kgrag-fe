import Image from "next/image";
import Upload from "./components/Upload";
import Modes from "./components/Modes";
import Settings from "./components/Settings";
import Suggestions from "./components/Suggestions";

export default function Home() {
  return (
    <main className="flex flex-col items-center pb-6 h-full min-h-screen pr-4">
      <div className="flex space-x-10">
        <div className="flex flex-col justify-between space-y-6 ml-12 w-1/4">
          <div>
            <Modes />
          </div>
          <div>
            <Settings />
          </div>
        </div>
        <Upload />
        <div id="right-panel">
          <Suggestions />
        </div>
      </div>
    </main>
  );
}
