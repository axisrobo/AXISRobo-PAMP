'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { getAuthToken } from '@/shared/lib/auth-token';

async function downloadAttachment(attachmentId: string, fileName: string) {
  const base = process.env.NEXT_PUBLIC_API_URL || '/api';
  const url = `${base}/ea-requests/attachments/${attachmentId}/download`;
  const token = getAuthToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
  const res = await fetch(url, { headers });
  if (!res.ok) return;

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

export function useRequestAttachments(requestId: string, messageApi: any) {
  const queryClient = useQueryClient();
  const [uploadAttachmentOpen, setUploadAttachmentOpen] = useState(false);
  const [uploadAttachmentFile, setUploadAttachmentFile] = useState<File | null>(null);

  const uploadAttachmentMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('requestId', requestId);
      formData.append('bizType', 'Proj_Intro');
      formData.append('originalName', file.name);
      const token = getAuthToken();
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const base = process.env.NEXT_PUBLIC_API_URL || '/api';
      const response = await fetch(`${base}/ea-requests/attachments/upload`, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Upload failed');
      }
      return response.json();
    },
    onSuccess: () => {
      setUploadAttachmentOpen(false);
      setUploadAttachmentFile(null);
      messageApi.success('Attachment uploaded successfully');
      queryClient.invalidateQueries({ queryKey: ['eaRequest', requestId] });
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Upload failed');
    },
  });

  const deleteAttachmentMutation = useMutation({
    mutationFn: (attachmentId: string) => api.delete(`/ea-requests/attachments/${attachmentId}`),
    onSuccess: () => {
      messageApi.success('Attachment deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['eaRequest', requestId] });
    },
    onError: () => {
      messageApi.error('Failed to delete attachment');
    },
  });

  const handleOpenUploadAttachmentModal = () => {
    setUploadAttachmentFile(null);
    setUploadAttachmentOpen(true);
  };

  const handleCloseUploadAttachmentModal = () => {
    setUploadAttachmentOpen(false);
    setUploadAttachmentFile(null);
  };

  const handleSaveUploadAttachment = () => {
    if (uploadAttachmentFile) {
      uploadAttachmentMutation.mutate(uploadAttachmentFile);
    }
  };

  return {
    uploadAttachmentOpen,
    uploadAttachmentFile,
    setUploadAttachmentFile,
    uploadAttachmentMutation,
    handleOpenUploadAttachmentModal,
    handleCloseUploadAttachmentModal,
    handleSaveUploadAttachment,
    handleDeleteAttachment: (attachmentId: string) => deleteAttachmentMutation.mutate(attachmentId),
    handleDownloadAttachment: downloadAttachment,
  };
}