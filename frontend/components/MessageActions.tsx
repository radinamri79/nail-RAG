import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react';

interface MessageActionsProps {
  messageId: string;
  content: string;
  onLike?: (messageId: string) => void;
  onDislike?: (messageId: string) => void;
  isLiked?: boolean;
  isDisliked?: boolean;
}

export const MessageActions: React.FC<MessageActionsProps> = ({
  messageId,
  content,
  onLike,
  onDislike,
  isLiked = false,
  isDisliked = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleLike = () => {
    onLike?.(messageId);
  };

  const handleDislike = () => {
    onDislike?.(messageId);
  };

  return (
    <div className="flex items-center gap-2 mt-2 text-gray-400">
      {/* Like Button */}
      <button
        onClick={handleLike}
        className={`p-2 rounded-lg transition-all duration-200 hover:bg-gray-100 group ${
          isLiked ? 'text-[#D98B99]' : 'text-gray-400 hover:text-gray-600'
        }`}
        title="Like this message"
      >
        <ThumbsUp
          className={`w-4 h-4 transition-all ${isLiked ? 'fill-current' : ''}`}
        />
      </button>

      {/* Dislike Button */}
      <button
        onClick={handleDislike}
        className={`p-2 rounded-lg transition-all duration-200 hover:bg-gray-100 ${
          isDisliked ? 'text-[#D98B99]' : 'text-gray-400 hover:text-gray-600'
        }`}
        title="Dislike this message"
      >
        <ThumbsDown
          className={`w-4 h-4 transition-all ${isDisliked ? 'fill-current' : ''}`}
        />
      </button>

      {/* Copy Button */}
      <button
        onClick={handleCopy}
        className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200"
        title="Copy message"
      >
        {copied ? (
          <Check className="w-4 h-4 text-green-500" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>

      {/* Copied feedback */}
      {copied && (
        <span className="text-xs text-green-500 font-medium animate-fade-in">
          Copied!
        </span>
      )}
    </div>
  );
};
