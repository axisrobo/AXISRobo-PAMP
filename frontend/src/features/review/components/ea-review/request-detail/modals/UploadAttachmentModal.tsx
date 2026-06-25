'use client';

import { Button, Modal, Space, Upload } from 'antd';
import { CloudUploadOutlined } from '@ant-design/icons';

type Props = {
  open: boolean;
  uploadAttachmentFile: File | null;
  setUploadAttachmentFile: (file: File | null) => void;
  isPending: boolean;
  onCancel: () => void;
  onSave: () => void;
};

export function UploadAttachmentModal({
  open,
  uploadAttachmentFile,
  setUploadAttachmentFile,
  isPending,
  onCancel,
  onSave,
}: Props) {
  return (
    <Modal
      title="Upload Attachment"
      open={open}
      onCancel={onCancel}
      footer={
        <Space>
          <Button onClick={onCancel}>Cancel</Button>
          <Button
            type="primary"
            disabled={!uploadAttachmentFile}
            loading={isPending}
            onClick={onSave}
          >
            Save
          </Button>
        </Space>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#E2231A' }}>*</span>{' '}
          Project Introduction (Reuse existing project materials for explanation.)
        </div>
        <Upload.Dragger
          multiple={false}
          beforeUpload={(file) => {
            setUploadAttachmentFile(file);
            return false;
          }}
          onRemove={() => setUploadAttachmentFile(null)}
          maxCount={1}
          fileList={uploadAttachmentFile ? [{ uid: '-1', name: uploadAttachmentFile.name, status: 'done' }] : []}
        >
          <p className="ant-upload-drag-icon">
            <CloudUploadOutlined style={{ fontSize: 40, color: '#40a9ff' }} />
          </p>
          <p className="ant-upload-text">
            Drag a file here, or <span style={{ color: '#1677ff' }}>click to upload</span>
          </p>
        </Upload.Dragger>
      </div>
    </Modal>
  );
}
