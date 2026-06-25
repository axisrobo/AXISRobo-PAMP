import React from 'react';

interface RichTextContentProps {
  html?: string | null;
  className?: string;
}

/**
 * Renders HTML content produced by RichTextEditor.
 * Uses dangerouslySetInnerHTML – content is trusted (created by our own editor).
 */
export function RichTextContent({ html, className }: RichTextContentProps) {
  if (!html || html === '<p></p>' || html.trim() === '') return null;

  return (
    <>
      <div
        className={className}
        dangerouslySetInnerHTML={{ __html: html }}
        style={{ wordBreak: 'break-word' }}
      />
      <style>{`
        .rich-content p { margin: 0 0 6px; }
        .rich-content ul, .rich-content ol { padding-left: 20px; margin: 4px 0; }
        .rich-content li { margin: 2px 0; }
        .rich-content strong { font-weight: 600; }
        .rich-content em { font-style: italic; }
        .rich-content s { text-decoration: line-through; }
        .rich-content img { max-width: 100%; height: auto; border-radius: 4px; margin: 4px 0; }
        .rich-content blockquote {
          border-left: 3px solid #d9d9d9;
          padding-left: 12px;
          margin: 4px 0;
          color: #595959;
        }
        .rich-content code {
          background: #f5f5f5;
          padding: 1px 4px;
          border-radius: 3px;
          font-family: monospace;
          font-size: 0.9em;
        }
      `}</style>
    </>
  );
}
