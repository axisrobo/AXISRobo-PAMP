'use client';

import { useState, useRef, useCallback } from 'react';
import { Upload, X, File, FileText, Image } from 'lucide-react';
import clsx from 'clsx';

export interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;      // 0-100
  status: 'pending' | 'uploading' | 'done' | 'error';
  errorMessage?: string;
}

interface FileUploadProps {
  files: UploadFile[];
  onFilesAdd: (newFiles: File[]) => void;
  onFileRemove: (fileId: string) => void;
  accept?: string;       // e.g. ".pdf,.docx,.xlsx"
  maxSize?: number;       // bytes, default 50MB
  maxFiles?: number;
  multiple?: boolean;
  className?: string;
  disabled?: boolean;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext ?? '')) return Image;
  if (['pdf', 'doc', 'docx', 'txt', 'rtf'].includes(ext ?? '')) return FileText;
  return File;
}

export function FileUpload({
  files,
  onFilesAdd,
  onFileRemove,
  accept,
  maxSize = 50 * 1024 * 1024,
  maxFiles = 10,
  multiple = true,
  className = '',
  disabled = false,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (incoming: FileList | File[]) => {
      const arr = Array.from(incoming);
      const valid = arr.filter((f) => f.size <= maxSize);
      if (valid.length === 0) return;
      const remaining = maxFiles - files.length;
      onFilesAdd(valid.slice(0, Math.max(0, remaining)));
    },
    [files.length, maxFiles, maxSize, onFilesAdd]
  );

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragActive(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (!disabled && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className={className}>
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          dragActive && !disabled ? 'border-primary-blue bg-blue-50/50' : 'border-border-light hover:border-primary-blue/60',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <Upload className="w-8 h-8 text-text-secondary mx-auto mb-2" />
        <p className="text-sm text-text-secondary">
          Drag a file here, or
          <span className="text-primary-blue font-medium">click to upload</span>
        </p>
        {accept && (
          <p className="text-xs text-text-secondary mt-1">
            Accepted: {accept}
          </p>
        )}
        <p className="text-xs text-text-secondary mt-1">Max {formatSize(maxSize)} per file</p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => { if (e.target.files) { handleFiles(e.target.files); e.target.value = ''; } }}
          className="hidden"
          disabled={disabled}
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-3 space-y-2">
          {files.map((f) => {
            const Icon = fileIcon(f.name);
            return (
              <div key={f.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg border border-border-light">
                <Icon className="w-5 h-5 text-text-secondary flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary truncate">{f.name}</p>
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <span>{formatSize(f.size)}</span>
                    {f.status === 'uploading' && <span className="text-primary-blue">Uploading {f.progress}%</span>}
                    {f.status === 'done' && <span className="text-green-600">Uploaded</span>}
                    {f.status === 'error' && <span className="text-red-500">{f.errorMessage || 'Upload failed'}</span>}
                  </div>
                  {f.status === 'uploading' && (
                    <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-primary-blue rounded-full transition-all" style={{ width: `${f.progress}%` }} />
                    </div>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onFileRemove(f.id); }}
                  className="flex-shrink-0 p-1 rounded hover:bg-gray-200 transition-colors"
                >
                  <X className="w-4 h-4 text-text-secondary" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
