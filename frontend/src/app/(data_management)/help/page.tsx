'use client';

import { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { api, fetchBlob } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';
import { Upload, FileText, Download, CheckCircle, Trash2 } from 'lucide-react';
import clsx from 'clsx';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

interface HelpFile {
  id: string;
  usage: string;
  fileName: string;
  filePath: string;
  createdBy?: string;
  createdAt?: string;
}

export default function HelpPage() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole('ea_admin');
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const { data: helpFiles } = useQuery({
    queryKey: ['helpFiles'],
    queryFn: () => api.get<HelpFile[]>('/master-data/help-files'),
  });

  const documents: HelpFile[] =
    helpFiles && helpFiles.length > 0
      ? helpFiles
      : [
          { id: '1', fileName: 'Certification Import&Export.xlsx', usage: 'Template', filePath: '' },
          { id: '2', fileName: 'EA Review.xlsx', usage: 'Template', filePath: '' },
          { id: '3', fileName: 'Application to Business Capability Mapping Operation Manual.pptx', usage: 'Guide', filePath: '' },
        ];

  // ── Upload mutation ──
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('usage', 'Template');
      return api.postForm<HelpFile>('/master-data/help-files/upload', formData);
    },
    onSuccess: () => {
      message.success('File uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['helpFiles'] });
    },
    onError: (err: Error) => {
      message.error(err.message || 'Upload failed');
    },
  });

  // ── Delete mutation ──
  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => api.delete(`/master-data/help-files/${fileId}`),
    onSuccess: () => {
      message.success('File deleted');
      queryClient.invalidateQueries({ queryKey: ['helpFiles'] });
    },
    onError: (err: Error) => {
      message.error(err.message || 'Delete failed');
    },
  });

  // ── File handling ──
  const handleFiles = useCallback(
    (fileList: FileList | File[]) => {
      const files = Array.from(fileList);
      for (const file of files) {
        if (file.size > MAX_FILE_SIZE) {
          message.error(`${file.name} exceeds 50 MB limit`);
          continue;
        }
        uploadMutation.mutate(file);
      }
    },
    [uploadMutation],
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleDownload = async (doc: HelpFile) => {
    if (!doc.filePath) return;
    try {
      const blob = await fetchBlob(`${API_BASE}/master-data/help-files/${doc.id}/download`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      message.error('Download failed');
    }
  };

  return (
    <div className="p-6">
      {/* Hero banner */}
      <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-red-500 rounded-lg p-8 mb-6 text-white overflow-hidden">
        <div className="relative z-10">
          <span className="inline-block px-3 py-1 text-xs font-medium border border-white/50 rounded mb-2">
            AxisArch Management
          </span>
          <h1 className="text-2xl font-bold">Support & Help</h1>
        </div>
      </div>

      {/* Guides & Templates section */}
      <div className="bg-white rounded-lg border border-border-light p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-2">Guides & Templates:</h2>
        <p className="text-sm text-text-secondary mb-6">
          Please find document for user guides and import template             for AxisArch Review, Meetings, Certification.
        </p>

        {/* Upload area - only visible to EA Admin */}
        {isAdmin && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={clsx(
              'border-2 border-dashed rounded-lg p-8 text-center mb-6 cursor-pointer transition-colors',
              dragActive
                ? 'border-primary-blue bg-blue-50/50'
                : 'border-border-default hover:border-primary-blue/60',
              uploadMutation.isPending && 'opacity-50 pointer-events-none',
            )}
          >
            <Upload className="w-10 h-10 text-text-secondary mx-auto mb-3 opacity-50" />
            <p className="text-sm text-text-secondary">
              {uploadMutation.isPending
                ? 'Uploading...'
                : (
                    <>
                      Drag a file here, or{' '}
                      <span className="text-primary-blue cursor-pointer hover:underline">click upload</span>
                    </>
                  )}
            </p>
            <input
              ref={inputRef}
              type="file"
              multiple
              onChange={(e) => {
                if (e.target.files) {
                  handleFiles(e.target.files);
                  e.target.value = '';
                }
              }}
              className="hidden"
            />
          </div>
        )}

        {/* Document list */}
        <div className="space-y-3 mb-6">
          {documents.map((doc) => (
            <div key={doc.id || doc.fileName} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <FileText className="w-5 h-5 text-text-secondary flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <span className="text-sm text-primary-blue hover:underline cursor-pointer font-medium">
                  {doc.fileName}
                </span>
                {doc.usage && (
                  <span className="ml-2 text-xs text-text-secondary bg-gray-100 px-2 py-0.5 rounded">
                    {doc.usage}
                  </span>
                )}
              </div>
              <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              <button
                className="text-text-secondary hover:text-primary-blue"
                onClick={() => handleDownload(doc)}
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
              {isAdmin && (
                <button
                  className="text-text-secondary hover:text-red-500"
                  onClick={() => deleteMutation.mutate(doc.id)}
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>

        {documents.length === 0 && (
          <p className="text-sm text-text-secondary text-center py-4">No help files available.</p>
        )}
      </div>
    </div>
  );
}
