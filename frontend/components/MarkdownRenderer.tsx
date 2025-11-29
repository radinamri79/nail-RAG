import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  // Split content into lines for processing
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip empty lines but add spacing
    if (!trimmed) {
      elements.push(<div key={`empty-${i}`} className="h-2" />);
      i++;
      continue;
    }

    // Check for numbered list items (1., 2., 3., etc.)
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
    if (numberedMatch) {
      const number = numberedMatch[1];
      const text = numberedMatch[2];
      elements.push(
        <div key={`numbered-${i}`} className="flex gap-3 mb-3">
          <span className="font-semibold text-[#D98B99] min-w-max">{number}.</span>
          <p className="flex-1 text-gray-700">{renderInlineMarkdown(text)}</p>
        </div>
      );
      i++;
      continue;
    }

    // Check for bullet points (-, *, •)
    const bulletMatch = trimmed.match(/^[-*•]\s+(.+)$/);
    if (bulletMatch) {
      const text = bulletMatch[1];
      elements.push(
        <div key={`bullet-${i}`} className="flex gap-3 mb-2 ml-2">
          <span className="text-[#D98B99] font-bold">•</span>
          <p className="flex-1 text-gray-700">{renderInlineMarkdown(text)}</p>
        </div>
      );
      i++;
      continue;
    }

    // Check for headers (# ## ###)
    const headerMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const text = headerMatch[2];
      const sizes = {
        1: 'text-xl font-bold',
        2: 'text-lg font-bold',
        3: 'text-base font-semibold',
      };
      const sizeClass = sizes[level as keyof typeof sizes] || sizes[3];
      elements.push(
        <h3 key={`header-${i}`} className={`${sizeClass} text-[#3D5A6C] mt-4 mb-2`}>
          {renderInlineMarkdown(text)}
        </h3>
      );
      i++;
      continue;
    }

    // Regular paragraph with inline markdown support
    elements.push(
      <p key={`para-${i}`} className="text-gray-700 mb-2 leading-relaxed">
        {renderInlineMarkdown(trimmed)}
      </p>
    );
    i++;
  }

  return (
    <div className="space-y-2">
      {elements}
    </div>
  );
};

// Helper function to render inline markdown (bold, italic, links, etc.)
function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  // Pattern to match **bold**, *italic*, `code`, and [link](url)
  const pattern = /\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\)/g;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    if (match[1]) {
      // Bold text **text**
      parts.push(
        <span key={`bold-${match.index}`} className="font-bold text-gray-900">
          {match[1]}
        </span>
      );
    } else if (match[2]) {
      // Italic text *text*
      parts.push(
        <span key={`italic-${match.index}`} className="italic text-gray-700">
          {match[2]}
        </span>
      );
    } else if (match[3]) {
      // Inline code `code`
      parts.push(
        <code key={`code-${match.index}`} className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-[#3D5A6C]">
          {match[3]}
        </code>
      );
    } else if (match[4] && match[5]) {
      // Link [text](url)
      parts.push(
        <a
          key={`link-${match.index}`}
          href={match[5]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#D98B99] hover:underline font-medium"
        >
          {match[4]}
        </a>
      );
    }

    lastIndex = pattern.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}
