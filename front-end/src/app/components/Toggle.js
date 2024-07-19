"use client";
import { useState } from "react";

const Toggle = ( { onToggle }) => {
  const [isOn, setIsOn] = useState(false);

  const toggle = () => {
    setIsOn(!isOn);
    onToggle();
  };

  return (
    <div className="flex items-center ">
      <button
        onClick={toggle}
        className={`${
          isOn ? "bg-blue-500" : "bg-gray-300"
        } relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none`}
      >
        <span
          className={`${
            isOn ? "translate-x-6" : "translate-x-1"
          } inline-block h-4 w-4 transform bg-white rounded-full transition-transform duration-200`}
        />
      </button>
    </div>
  );
};

export default Toggle;
