'use client';

import { Modal } from 'antd';
import { AlertTriangle, Info, Trash2 } from 'lucide-react';

type DialogVariant = 'danger' | 'warning' | 'info';

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: DialogVariant;
  loading?: boolean;
}

const variantConfig: Record<DialogVariant, { icon: typeof AlertTriangle; iconBg: string; iconColor: string; okType: 'primary' | 'default'; okDanger: boolean }> = {
  danger: {
    icon: Trash2,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    okType: 'primary',
    okDanger: true,
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    okType: 'primary',
    okDanger: false,
  },
  info: {
    icon: Info,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    okType: 'primary',
    okDanger: false,
  },
};

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
}: ConfirmDialogProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <Modal
      open={open}
      onCancel={onClose}
      onOk={onConfirm}
      title={
        <div className="flex items-center gap-3">
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${config.iconBg}`}>
            <Icon className={`w-4 h-4 ${config.iconColor}`} />
          </div>
          <span>{title}</span>
        </div>
      }
      okText={confirmLabel}
      cancelText={cancelLabel}
      okType={config.okType}
      okButtonProps={{ danger: config.okDanger, loading }}
      cancelButtonProps={{ disabled: loading }}
      maskClosable
      destroyOnHidden
      centered
      width={440}
    >
      <div className="text-sm text-text-secondary ml-11">{message}</div>
    </Modal>
  );
}
