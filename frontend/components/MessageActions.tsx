import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react';

interface MessageActionsProps {
  messageId: string;
  content: string;
  role: 'user' | 'assistant';
  onLike?: (messageId: string) => void;
  onDislike?: (messageId: string) => void;
  isLiked?: boolean;
  isDisliked?: boolean;
}

export const MessageActions: React.FC<MessageActionsProps> = ({
  messageId,
  content,
  role,
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
    // If already liked, toggle it off. If not liked but disliked, clear dislike first
    if (isLiked) {
      onLike?.(messageId); // Toggle off
    } else {
      // Clear dislike if it's active, then set like
      if (isDisliked) {
        onDislike?.(messageId); // Clear dislike
      }
      onLike?.(messageId); // Set like
    }
  };

  const handleDislike = () => {
    // If already disliked, toggle it off. If not disliked but liked, clear like first
    if (isDisliked) {
      onDislike?.(messageId); // Toggle off
    } else {
      // Clear like if it's active, then set dislike
      if (isLiked) {
        onLike?.(messageId); // Clear like
      }
      onDislike?.(messageId); // Set dislike
    }
  };

  // Only show copy for user messages
  if (role === 'user') {
    return (
      <div className="flex items-center gap-2 mt-2 text-gray-400">
        {/* Copy Button - User messages only */}
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
  }

  // AI assistant messages - show like, dislike and copy
  return (
    <div className="flex items-center gap-2 mt-2 text-gray-400">
      {/* Like Button - AI messages only */}
      <button
        onClick={handleLike}
        className={`p-2 rounded-lg transition-all duration-200 hover:bg-gray-100 ${
          isLiked
            ? 'text-[#D98B99]'
            : 'text-gray-400 hover:text-gray-600'
        }`}
        title={isLiked ? 'Unlike this message' : 'Like this message'}
      >
        <ThumbsUp
          className={`w-4 h-4 transition-all ${isLiked ? 'fill-current' : ''}`}
        />
      </button>

      {/* Dislike Button - AI messages only */}
      <button
        onClick={handleDislike}
        className={`p-2 rounded-lg transition-all duration-200 hover:bg-gray-100 ${
          isDisliked
            ? 'text-[#D98B99]'
            : 'text-gray-400 hover:text-gray-600'
        }`}
        title={isDisliked ? 'Remove dislike' : 'Dislike this message'}
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
