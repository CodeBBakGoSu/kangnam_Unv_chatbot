import React, { useState, useRef, useEffect } from 'react';

const AgentChat = () => {
  const [inputValue, setInputValue] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const chatContainerRef = useRef(null);

  const recommendedQuestions = [
    '소프트웨어 과목 찾아줘',
    '경영학과 졸업 하려면 어떻게 해야해??',
    '교수님 이메일이 뭐야??',
  ];

  useEffect(() => {
    // Scroll to the bottom of the chat container when new messages are added
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;

    const userMessage = { text: inputValue, sender: 'user' };

    // Simulate a bot response for demonstration
    const botMessage = { text: `'${inputValue}'에 대한 답변을 찾고 있습니다...`, sender: 'bot' };

    setChatMessages([...chatMessages, userMessage, botMessage]);

    // TODO: Replace simulation with actual API call

    setInputValue('');
  };

  const handleRecommendationClick = (question) => {
    setInputValue(question);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen w-full flex-col bg-gradient-to-br from-sky-100 to-sky-200 dark:from-sky-800 dark:to-sky-900 font-display text-gray-800 dark:text-gray-200">
      <div className="flex flex-1 flex-col items-center justify-between p-4 md:p-6 lg:p-10">
        {chatMessages.length === 0 ? (
          // Initial View
          <div className="flex w-full max-w-2xl flex-col items-center justify-center gap-10 flex-1">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white">강남대학교 챗봇 강냉이</h1>
            <div className="w-full">
              <div className="mb-4 flex flex-wrap justify-center gap-3">
                {recommendedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleRecommendationClick(question)}
                    className="flex min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-full h-10 px-4 bg-white/50 dark:bg-black/20 backdrop-blur-sm border border-white/60 dark:border-white/20 text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-white/70 dark:hover:bg-black/30 transition-colors"
                  >
                    <span className="truncate">{question}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Chat View
          <div ref={chatContainerRef} className="w-full max-w-2xl flex-1 overflow-y-auto mb-4">
            {chatMessages.map((message, index) => (
              <div key={index} className={`flex my-2 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`rounded-lg px-4 py-2 max-w-lg ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                  {message.text}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="w-full max-w-2xl">
          <div className="relative flex items-center">
            <input
              value={inputValue}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white py-4 pl-5 pr-14 text-base focus:ring-2 focus:ring-[#4682B4] focus:border-[#4682B4] transition-shadow shadow-lg"
              placeholder="강냉이에게 무엇이든 물어보세요..."
              type="text"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="absolute right-3 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#87CEEB] to-[#4682B4] text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentChat;