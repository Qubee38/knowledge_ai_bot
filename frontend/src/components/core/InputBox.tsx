import { FC, useState, KeyboardEvent } from 'react';
import './InputBox.css';

interface InputBoxProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  sampleQueries?: string[];
}

export const InputBox: FC<InputBoxProps> = ({ 
  onSend, 
  disabled = false, 
  placeholder = "メッセージを入力...",
  sampleQueries = []
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-box">
      <div className="input-container">
        <textarea
          className="input-textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, 200) + 'px';
          }}
        />
        
        <div className="input-actions">
          <button
            className="send-button"
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            title="送信 (Enter)"
          >
            {disabled ? '⏳' : '📤'}
          </button>
        </div>
      </div>
      
      {!disabled && input.length === 0 && sampleQueries.length > 0 && (
        <div className="input-suggestions">
          <span className="suggestions-label">試してみる:</span>
          {sampleQueries.slice(0, 3).map((query, index) => (
            <button
              key={index}
              className="suggestion-chip"
              onClick={() => setInput(query)}
            >
              {query}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};