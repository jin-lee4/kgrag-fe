"use client"; // Add this line

import React, { useState } from 'react';

const Suggestion = ({ borderColor, title, description }) => {
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  const handleChatChange = (e) => {
    setChatMessage(e.target.value);
  };

  const handleSubmit = () => {
    // Add your submit logic here
    setChatHistory([...chatHistory, { text: chatMessage, sender: 'user' }]);
    setChatMessage('');
  };

  const handleCancel = () => {
    setChatMessage('');
  };

  return (
    <div
      id="suggestion-container"
      style={{ border: `3px solid ${borderColor}`, padding: '16px', borderRadius: '8px', maxWidth: '500px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}
    >
      <div>
        <p className="small-text" style={{ fontWeight: 'bold', marginBottom: '8px' }}>{title}</p>
      </div>
      <div id="suggestion-text"><p>{description}</p></div>
      <div style={{ marginTop: '13px', flex: '1 1 auto' }}>
        <div style={{ marginBottom: '13px', padding: '8px 0', maxHeight: '200px', overflowY: 'auto' }}>
          {chatHistory.map((message, index) => (
            <div key={index} style={{ marginBottom: '8px', textAlign: message.sender === 'user' ? 'right' : 'left', fontFamily: 'inherit', fontSize: 'inherit', color: 'inherit', fontWeight: 'normal' }}>
            {message.text}
            </div>
          ))}
        </div>
        <input
          type="text"
          value={chatMessage}
          onChange={handleChatChange}
          placeholder="Ask ruleaid..."
          style={{
            width: '335px',
            padding: '8px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            marginBottom: '16px',
            boxSizing: 'border-box' // Ensure the padding is included in the width
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button
            onClick={handleCancel}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: '#555',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            style={{
              backgroundColor: '#333',
              border: 'none',
              color: '#fff',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};

export default Suggestion;
