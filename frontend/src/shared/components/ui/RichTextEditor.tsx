'use client';

import { useEditor, EditorContent, NodeViewWrapper, ReactNodeViewRenderer } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import { Color } from '@tiptap/extension-color';
import { TextStyle } from '@tiptap/extension-text-style';
import Link from '@tiptap/extension-link';
import { useCallback, useRef, useEffect, useState } from 'react';
import { Button, Select, Tooltip, Popover, Input } from 'antd';
import {
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  StrikethroughOutlined,
  OrderedListOutlined,
  UnorderedListOutlined,
  PictureOutlined,
  FontColorsOutlined,
  ClearOutlined,
  UndoOutlined,
  RedoOutlined,
  LinkOutlined,
  DisconnectOutlined,
} from '@ant-design/icons';

/* ── FontSize Extension ─────────────────────────────────────── */
const FontSize = TextStyle.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      fontSize: {
        default: null,
        parseHTML: (element: HTMLElement) => element.style.fontSize?.replace('px', '') || null,
        renderHTML: (attributes: Record<string, unknown>) => {
          if (!attributes.fontSize) return {};
          return { style: `font-size: ${attributes.fontSize}px` };
        },
      },
    };
  },
  addCommands() {
    return {
      ...this.parent?.(),
      setFontSize:
        (fontSize: string) =>
        ({ chain }: any) => {
          return chain().setMark('textStyle', { fontSize }).run();
        },
      unsetFontSize:
        () =>
        ({ chain }: any) => {
          return chain().setMark('textStyle', { fontSize: null }).run();
        },
    } as any;
  },
});

/* ── Toolbar color swatches ────────────────────────────────── */
const COLORS = [
  '#000000', '#e2231a', '#fa8c16', '#fadb14', '#52c41a',
  '#1677ff', '#722ed1', '#eb2f96', '#595959', '#8c8c8c',
  '#ffffff', '#ffa39e', '#ffd591', '#fffb8f', '#b7eb8f',
  '#91caff', '#d3adf7', '#ffadd2',
];

const FONT_SIZES = ['12', '14', '16', '18', '20', '24', '28', '32'];

/* ── ResizableImage Node View — selection highlight + drag-to-resize ── */
function ResizableImageView(props: any) {
  const { node, updateAttributes, selected } = props;
  const { src, alt, title, width } = node.attrs;
  const imgRef = useRef<HTMLImageElement>(null);

  const startResize = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const startX = e.clientX;
      const startWidth = imgRef.current?.offsetWidth ?? 200;

      const onMouseMove = (ev: MouseEvent) => {
        const newWidth = Math.max(50, startWidth + (ev.clientX - startX));
        updateAttributes({ width: `${Math.round(newWidth)}px` });
      };
      const onMouseUp = () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },
    [updateAttributes],
  );

  return (
    <NodeViewWrapper
      as="div"
      style={{
        display: 'inline-block',
        position: 'relative',
        lineHeight: 0,
        maxWidth: '100%',
        margin: '4px 0',
      }}
    >
      <img
        ref={imgRef}
        src={src}
        alt={alt || ''}
        title={title}
        style={{
          display: 'block',
          width: width || 'auto',
          maxWidth: '100%',
          height: 'auto',
          borderRadius: 4,
          cursor: 'default',
          outline: selected ? '2px solid #1677ff' : 'none',
          boxShadow: selected ? '0 0 0 3px rgba(22,119,255,0.15)' : 'none',
        }}
      />
      {selected && (
        <span
          onMouseDown={startResize}
          title="Drag to resize"
          style={{
            position: 'absolute',
            right: -6,
            bottom: -6,
            width: 12,
            height: 12,
            background: '#1677ff',
            border: '2px solid #fff',
            borderRadius: 2,
            cursor: 'se-resize',
            display: 'block',
            zIndex: 10,
          }}
        />
      )}
    </NodeViewWrapper>
  );
}

/* ── ResizableImage Extension — width stored as CSS style ── */
const ResizableImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: (element: HTMLElement) =>
          element.style.width || element.getAttribute('width') || null,
        renderHTML: (attributes: Record<string, unknown>) => {
          if (!attributes.width) return {};
          return { style: `width: ${attributes.width}; height: auto;` };
        },
      },
    };
  },
  addNodeView() {
    return ReactNodeViewRenderer(ResizableImageView);
  },
});

interface RichTextEditorProps {
  value?: string;
  onChange?: (html: string) => void;
  placeholder?: string;
  minHeight?: number;
}

export function RichTextEditor({
  value = '',
  onChange,
  placeholder = 'Enter content here...',
  minHeight = 180,
}: RichTextEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const colorInputRef = useRef<HTMLInputElement>(null);
  const isInternalChange = useRef(false);
  const [isImageSelected, setIsImageSelected] = useState(false);
  const [linkPopoverOpen, setLinkPopoverOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState('');

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({ dropcursor: false, link: false }),
      FontSize,
      Color,
      ResizableImage.configure({ inline: false, allowBase64: true }),
      Link.configure({ openOnClick: false, HTMLAttributes: { target: '_blank', rel: 'noopener noreferrer' } }),
    ],
    content: value,
    onUpdate({ editor }) {
      isInternalChange.current = true;
      onChange?.(editor.getHTML());
      setIsImageSelected(editor.isActive('image'));
    },
    onSelectionUpdate({ editor }) {
      setIsImageSelected(editor.isActive('image'));
      // Pre-fill link URL when cursor is inside a link
      if (editor.isActive('link')) {
        setLinkUrl(editor.getAttributes('link').href || '');
      }
    },
    editorProps: {
      attributes: {
        class: 'rich-editor-body',
        style: `min-height:${minHeight}px; outline:none; padding:12px; box-sizing:border-box;`,
      },
    },
  });

  /* Sync external value changes (e.g., when form resets) */
  useEffect(() => {
    if (!editor) return;
    if (isInternalChange.current) {
      isInternalChange.current = false;
      return;
    }
    const current = editor.getHTML();
    if (current !== value) {
      editor.commands.setContent(value || '', { emitUpdate: false });
    }
  }, [value, editor]);

  /* Image upload handler — converts to base64 so images display without auth headers */
  const handleImageUpload = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string;
        if (dataUrl) {
          editor?.chain().focus().setImage({ src: dataUrl, alt: file.name }).run();
        }
      };
      reader.readAsDataURL(file);
    },
    [editor],
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleImageUpload(file);
    e.target.value = '';
  };

  const handleColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    editor?.chain().focus().setColor(e.target.value).run();
  };

  const currentFontSize = editor?.getAttributes('textStyle')?.fontSize ?? '';

  if (!editor) return null;

  const btnStyle = (active: boolean) => ({
    color: active ? '#1677ff' : undefined,
    background: active ? '#e6f4ff' : undefined,
  });

  return (
    <div
      style={{
        position: 'relative',
        border: '1px solid #d9d9d9',
        borderRadius: 8,
        overflow: 'hidden',
        background: '#fff',
      }}
    >
      {/* ── Toolbar ── */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 2,
          padding: '6px 8px',
          borderBottom: '1px solid #f0f0f0',
          background: '#fafafa',
        }}
      >
        {/* Undo / Redo */}
        <Tooltip title="Undo">
          <Button
            type="text"
            size="small"
            icon={<UndoOutlined />}
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
          />
        </Tooltip>
        <Tooltip title="Redo">
          <Button
            type="text"
            size="small"
            icon={<RedoOutlined />}
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
          />
        </Tooltip>

        <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />

        {/* Font Size */}
        <Select
          size="small"
          style={{ width: 72 }}
          placeholder="Font Size"
          value={currentFontSize || undefined}
          onChange={(val) => {
            if (val) {
              (editor.chain().focus() as any).setFontSize(val).run();
            } else {
              (editor.chain().focus() as any).unsetFontSize().run();
            }
          }}
          allowClear
          options={FONT_SIZES.map((s) => ({ label: `${s}px`, value: s }))}
          getPopupContainer={(n) => n.parentElement || document.body}
        />

        <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />

        {/* Bold */}
        <Tooltip title="Bold">
          <Button
            type="text"
            size="small"
            icon={<BoldOutlined />}
            onClick={() => editor.chain().focus().toggleBold().run()}
            style={btnStyle(editor.isActive('bold'))}
          />
        </Tooltip>

        {/* Italic */}
        <Tooltip title="Italic">
          <Button
            type="text"
            size="small"
            icon={<ItalicOutlined />}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            style={btnStyle(editor.isActive('italic'))}
          />
        </Tooltip>

        {/* Underline */}
        <Tooltip title="Underline">
          <Button
            type="text"
            size="small"
            icon={<UnderlineOutlined />}
            onClick={() => editor.chain().focus().toggleUnderline?.().run()}
            style={btnStyle(editor.isActive('underline'))}
          />
        </Tooltip>

        {/* Strike */}
        <Tooltip title="Strikethrough">
          <Button
            type="text"
            size="small"
            icon={<StrikethroughOutlined />}
            onClick={() => editor.chain().focus().toggleStrike().run()}
            style={btnStyle(editor.isActive('strike'))}
          />
        </Tooltip>

        <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />

        {/* Unordered List */}
        <Tooltip title="Bullet List">
          <Button
            type="text"
            size="small"
            icon={<UnorderedListOutlined />}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            style={btnStyle(editor.isActive('bulletList'))}
          />
        </Tooltip>

        {/* Ordered List */}
        <Tooltip title="Numbered List">
          <Button
            type="text"
            size="small"
            icon={<OrderedListOutlined />}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            style={btnStyle(editor.isActive('orderedList'))}
          />
        </Tooltip>

        <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />

        {/* Text Color */}
        <Tooltip title="Text Color">
          <div style={{ position: 'relative', display: 'inline-flex' }}>
            <Button
              type="text"
              size="small"
              icon={
                <span style={{ position: 'relative', display: 'inline-block' }}>
                  <FontColorsOutlined />
                  <span
                    style={{
                      position: 'absolute',
                      bottom: -2,
                      left: 0,
                      right: 0,
                      height: 3,
                      background: editor.getAttributes('textStyle')?.color || '#000',
                      borderRadius: 1,
                    }}
                  />
                </span>
              }
              onClick={() => colorInputRef.current?.click()}
            />
            <input
              ref={colorInputRef}
              type="color"
              style={{ position: 'absolute', opacity: 0, width: 0, height: 0, pointerEvents: 'none' }}
              onChange={handleColorChange}
            />
          </div>
        </Tooltip>

        {/* Color Swatches */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2, maxWidth: 120 }}>
          {COLORS.slice(0, 10).map((c) => (
            <button
              key={c}
              title={c}
              onClick={() => editor.chain().focus().setColor(c).run()}
              style={{
                width: 14,
                height: 14,
                borderRadius: 2,
                background: c,
                border: editor.getAttributes('textStyle')?.color === c ? '2px solid #1677ff' : '1px solid #d9d9d9',
                cursor: 'pointer',
                padding: 0,
              }}
            />
          ))}
        </div>

        <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />

        {/* Insert Image */}
        <Tooltip title="Insert Image">
          <Button
            type="text"
            size="small"
            icon={<PictureOutlined />}
            onClick={() => fileInputRef.current?.click()}
          />
        </Tooltip>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {/* Insert / Edit Link */}
        <Popover
          open={linkPopoverOpen}
          onOpenChange={(open) => {
            if (open) {
              // Pre-fill with existing link href if any
              setLinkUrl(editor.isActive('link') ? (editor.getAttributes('link').href || '') : '');
            }
            setLinkPopoverOpen(open);
          }}
          trigger="click"
          placement="bottomLeft"
          title="Insert Link"
          content={
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: 280 }}>
              <Input
                size="small"
                placeholder="Enter URL, e.g. https://example.com"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onPressEnter={() => {
                  const url = linkUrl.trim();
                  if (url) {
                    const href = url.startsWith('http') ? url : `https://${url}`;
                    editor.chain().focus().extendMarkRange('link').setLink({ href }).run();
                  } else {
                    editor.chain().focus().extendMarkRange('link').unsetLink().run();
                  }
                  setLinkPopoverOpen(false);
                }}
                autoFocus
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                <Button size="small" onClick={() => setLinkPopoverOpen(false)}>Cancel</Button>
                <Button
                  size="small"
                  type="primary"
                  onClick={() => {
                    const url = linkUrl.trim();
                    if (url) {
                      const href = url.startsWith('http') ? url : `https://${url}`;
                      editor.chain().focus().extendMarkRange('link').setLink({ href }).run();
                    } else {
                      editor.chain().focus().extendMarkRange('link').unsetLink().run();
                    }
                    setLinkPopoverOpen(false);
                  }}
                >
                  Confirm
                </Button>
              </div>
            </div>
          }
          getPopupContainer={(n) => n.parentElement || document.body}
        >
          <Tooltip title={editor.isActive('link') ? 'Edit Link' : 'Insert Link'}>
            <Button
              type="text"
              size="small"
              icon={<LinkOutlined />}
              style={btnStyle(editor.isActive('link'))}
            />
          </Tooltip>
        </Popover>

        {/* Unset Link */}
        {editor.isActive('link') && (
          <Tooltip title="Remove Link">
            <Button
              type="text"
              size="small"
              icon={<DisconnectOutlined />}
              onClick={() => editor.chain().focus().extendMarkRange('link').unsetLink().run()}
            />
          </Tooltip>
        )}

        {/* Clear Formatting */}
        <Tooltip title="Clear Formatting">
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={() => editor.chain().focus().clearNodes().unsetAllMarks().run()}
          />
        </Tooltip>

        {/* Image controls — shown when an image is selected */}
        {isImageSelected && (
          <>
            <span style={{ width: 1, height: 18, background: '#e8e8e8', margin: '0 4px' }} />
            <span style={{ fontSize: 12, color: '#595959', whiteSpace: 'nowrap' }}>Image:</span>
            {(['30%', '50%', '100%'] as const).map((pct) => (
              <Button
                key={pct}
                type="text"
                size="small"
                style={{ fontSize: 12, padding: '0 5px', minWidth: 'unset' }}
                onClick={() =>
                  editor.chain().focus().updateAttributes('image', { width: pct }).run()
                }
              >
                {pct}
              </Button>
            ))}
            <Tooltip title="Reset Size">
              <Button
                type="text"
                size="small"
                style={{ fontSize: 12, padding: '0 5px', minWidth: 'unset' }}
                onClick={() =>
                  editor.chain().focus().updateAttributes('image', { width: null }).run()
                }
              >
                Reset
              </Button>
            </Tooltip>
            <Tooltip title="Delete Image">
              <Button
                type="text"
                size="small"
                danger
                style={{ fontSize: 12, padding: '0 5px', minWidth: 'unset' }}
                onClick={() => editor.chain().focus().deleteSelection().run()}
              >
                Delete
              </Button>
            </Tooltip>
          </>
        )}
      </div>

      {/* ── Editor Area ── */}
      <EditorContent editor={editor} />

      {/* Placeholder overlay */}
      {editor.isEmpty && !value?.replace(/<[^>]*>/g, '').trim() && (
        <div
          style={{
            position: 'absolute',
            top: 56,
            left: 12,
            color: '#bfbfbf',
            pointerEvents: 'none',
            fontSize: 14,
            userSelect: 'none',
          }}
        >
          {placeholder}
        </div>
      )}

      {/* ── Global styles injected via style tag ── */}
      <style>{`
        .rich-editor-body {
          font-size: 14px;
          line-height: 1.6;
          color: #333;
          word-break: break-word;
        }
        .rich-editor-body p { margin: 0 0 6px; }
        .rich-editor-body ul, .rich-editor-body ol { padding-left: 20px; margin: 4px 0; }
        .rich-editor-body li { margin: 2px 0; }
        .rich-editor-body strong { font-weight: 600; }
        .rich-editor-body em { font-style: italic; }
        .rich-editor-body s { text-decoration: line-through; }
        .rich-editor-body img { max-width: 100%; height: auto; border-radius: 4px; }
        .rich-editor-body a { color: #1677ff; text-decoration: underline; cursor: pointer; }
        .rich-editor-body a:hover { color: #4096ff; }
        .rich-editor-body .ProseMirror-focused { outline: none; }
        .rich-editor-body blockquote {
          border-left: 3px solid #d9d9d9;
          padding-left: 12px;
          margin: 4px 0;
          color: #595959;
        }
        .rich-editor-body code {
          background: #f5f5f5;
          padding: 1px 4px;
          border-radius: 3px;
          font-family: monospace;
          font-size: 0.9em;
        }
      `}</style>
    </div>
  );
}
