"use client"; // Add this line

import React from 'react';
import Suggestion from "./Suggestion"; // Correct import

const Suggestions = () => {
  return (
    <div className="space-y-3.5">
      <Suggestion
        borderColor="#e08072"
        title="Compare"
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua."
      />
      <Suggestion
        borderColor="#7cc287"
        title="Clarify"
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua."
      />
      <Suggestion
        borderColor="#9d87d9"
        title="Analyse"
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua."
      />
    </div>
  );
};

export default Suggestions;
