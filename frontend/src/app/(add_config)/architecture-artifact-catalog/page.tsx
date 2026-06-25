'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Download, Edit3, Plus, RefreshCw, RotateCcw, Save, Trash2 } from 'lucide-react';

import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';
import {
  ArtifactCatalogConfig,
  ArtifactCatalogItem,
  emptyArtifactCatalogConfig,
  mergeArtifactCatalogConfig,
} from '@/features/review/config/artifactCatalogConfig';

type ArtifactCatalogConfigResponse = {
  configKey: string;
  version: number;
  config: Record<string, unknown>;
  changeNote?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  source: 'db' | 'default';
};

type ArtifactCatalogFormValues = {
  key: string;
  name: string;
  purpose: string;
  typicalContentsText: string;
  isActive: boolean;
  sortOrder: number;
};

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function splitLines(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toFormValues(item?: ArtifactCatalogItem): ArtifactCatalogFormValues {
  return {
    key: item?.key || '',
    name: item?.name || '',
    purpose: item?.purpose || '',
    typicalContentsText: item?.typicalContents?.join('\n') || '',
    isActive: item?.isActive ?? true,
    sortOrder: item?.sortOrder || 1,
  };
}

function nextSortOrder(items: ArtifactCatalogItem[]): number {
  return Math.max(0, ...items.map((item) => item.sortOrder || 0)) + 1;
}

function sortItems(items: ArtifactCatalogItem[]): ArtifactCatalogItem[] {
  return [...items].sort((left, right) => left.sortOrder - right.sortOrder || left.name.localeCompare(right.name));
}

export default function ArchitectureArtifactCatalogPage() {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm<ArtifactCatalogFormValues>();
  const isAdmin = hasRole('ea_admin');

  const [config, setConfig] = useState<ArtifactCatalogConfig>(() => ({
    ...emptyArtifactCatalogConfig,
    artifactTypes: [],
  }));
  const [changeNote, setChangeNote] = useState('');
  const [searchText, setSearchText] = useState('');
  const [showInactive, setShowInactive] = useState(true);
  const [editingItem, setEditingItem] = useState<ArtifactCatalogItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['architectureArtifactCatalogConfig', 'default', 'adminPage'],
    queryFn: () => api.get<ArtifactCatalogConfigResponse>('/avdm/artifact-catalog-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const serverConfig = useMemo(() => mergeArtifactCatalogConfig(data?.config || {}), [data?.config]);

  useEffect(() => {
    if (!data) {
      return;
    }
    setConfig(serverConfig);
  }, [data, serverConfig]);

  const filteredItems = useMemo(() => {
    const needle = searchText.trim().toLowerCase();
    return sortItems(config.artifactTypes).filter((item) => {
      if (!showInactive && !item.isActive) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return [
        item.key,
        item.name,
        item.purpose,
        ...item.typicalContents,
      ].some((value) => value.toLowerCase().includes(needle));
    });
  }, [config.artifactTypes, searchText, showInactive]);

  const saveMutation = useMutation({
    mutationFn: async () => api.put<ArtifactCatalogConfigResponse>(
      '/avdm/artifact-catalog-config?configKey=default',
      {
        config: mergeArtifactCatalogConfig(config),
        changeNote: changeNote || null,
        operator: user?.id || 'system',
      }
    ),
    onSuccess: () => {
      messageApi.success('Architecture artifact catalog saved.');
      queryClient.invalidateQueries({ queryKey: ['architectureArtifactCatalogConfig'] });
      setChangeNote('');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save architecture artifact catalog');
    },
  });

  const openEditor = (item?: ArtifactCatalogItem) => {
    const initial = item || {
      key: '',
      name: '',
      purpose: '',
      typicalContents: [],
      supportedViewpoints: [],
      isActive: true,
      sortOrder: nextSortOrder(config.artifactTypes),
    };
    setEditingItem(item || null);
    form.setFieldsValue(toFormValues(initial));
    setModalOpen(true);
  };

  const saveItem = async () => {
    const values = await form.validateFields();
    const normalized: ArtifactCatalogItem = {
      key: values.key.trim(),
      name: values.name.trim(),
      purpose: values.purpose.trim(),
      typicalContents: splitLines(values.typicalContentsText),
      supportedViewpoints: editingItem?.supportedViewpoints || [],
      isActive: values.isActive,
      sortOrder: Number(values.sortOrder) || nextSortOrder(config.artifactTypes),
    };

    setConfig((previous) => {
      const exists = previous.artifactTypes.some((item) => item.key === normalized.key);
      return {
        ...previous,
        artifactTypes: sortItems(
          exists
            ? previous.artifactTypes.map((item) => item.key === normalized.key ? normalized : item)
            : [...previous.artifactTypes, normalized]
        ),
      };
    });
    setModalOpen(false);
    setEditingItem(null);
  };

  const deleteItem = (key: string) => {
    setConfig((previous) => ({
      ...previous,
      artifactTypes: previous.artifactTypes.filter((item) => item.key !== key),
    }));
  };

  const updateItemStatus = (key: string, isActive: boolean) => {
    setConfig((previous) => ({
      ...previous,
      artifactTypes: previous.artifactTypes.map((item) => item.key === key ? { ...item, isActive } : item),
    }));
  };

  const columns: ColumnsType<ArtifactCatalogItem> = [
    {
      title: 'Order',
      dataIndex: 'sortOrder',
      width: 84,
      sorter: (a, b) => a.sortOrder - b.sortOrder,
    },
    {
      title: 'Artifact',
      dataIndex: 'name',
      width: 260,
      render: (value: string, record) => (
        <div>
          <div className="font-medium text-slate-900">{value}</div>
          <div className="mt-1 text-xs text-slate-500">{record.key}</div>
        </div>
      ),
    },
    {
      title: 'Purpose',
      dataIndex: 'purpose',
      ellipsis: true,
    },
    {
      title: 'Typical Contents',
      dataIndex: 'typicalContents',
      width: 260,
      render: (items: string[]) => (
        <Space size={[4, 4]} wrap>
          {items.map((item) => <Tag key={item}>{item}</Tag>)}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'isActive',
      width: 120,
      render: (value: boolean, record) => (
        <Switch
          checked={value}
          checkedChildren="Active"
          unCheckedChildren="Inactive"
          onChange={(checked) => updateItemStatus(record.key, checked)}
        />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 112,
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openEditor(record)} />
          <Popconfirm title="Delete artifact definition?" onConfirm={() => deleteItem(record.key)}>
            <Button danger icon={<Trash2 className="h-4 w-4" />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (!isAdmin) {
    return (
      <div className="p-6">
        {contextHolder}
        <Alert
          type="error"
          showIcon
          message="Access denied"
          description="Only EA Admin can maintain the architecture artifact catalog."
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {contextHolder}

      <section className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Typography.Title level={4} style={{ marginBottom: 4 }}>Architecture Artifact Catalog</Typography.Title>
            <Typography.Text type="secondary">
              Maintain preparation-stage artifact definitions through the backend AVDM config source of truth. Viewpoint-to-artifact relationships are governed in the dedicated mapping guide.
            </Typography.Text>
          </div>
          <Space wrap>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>
              Refresh
            </Button>
            <Button
              icon={<RotateCcw className="h-4 w-4" />}
              onClick={() => {
                setConfig(serverConfig);
                setChangeNote('');
              }}
            >
              Reset Server Config
            </Button>
            <Button
              icon={<Download className="h-4 w-4" />}
              onClick={() => downloadJson(
                `architecture-artifact-catalog-${new Date().toISOString().slice(0, 10)}.json`,
                mergeArtifactCatalogConfig(config)
              )}
            >
              Export JSON
            </Button>
            <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
              Save Catalog
            </Button>
          </Space>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(220px,1.4fr)_220px_minmax(260px,1fr)]">
        <Input
          value={config.catalogName}
          onChange={(event) => setConfig((previous) => ({ ...previous, catalogName: event.target.value }))}
          placeholder="Catalog name"
        />
        <Input value={config.stage} disabled />
        <Input
          value={changeNote}
          onChange={(event) => setChangeNote(event.target.value)}
          placeholder="Change note for this version"
        />
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(260px,1fr)_180px_auto]">
        <Input.Search
          allowClear
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Search artifact, purpose, content"
        />
        <div className="flex items-center gap-2 rounded border border-slate-200 bg-white px-3">
          <Switch checked={showInactive} onChange={setShowInactive} />
          <span className="text-sm text-slate-600">Show inactive</span>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openEditor()}>
          Add Artifact
        </Button>
      </div>

      <Table<ArtifactCatalogItem>
        rowKey="key"
        loading={isLoading}
        columns={columns}
        dataSource={filteredItems}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 1120 }}
      />

      <Modal
        title={editingItem ? `Edit ${editingItem.name}` : 'Add Architecture Artifact'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingItem(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        destroyOnHidden
        width={760}
      >
        <Form<ArtifactCatalogFormValues>
          form={form}
          layout="vertical"
          onFinish={saveItem}
          initialValues={{ isActive: true, sortOrder: nextSortOrder(config.artifactTypes) }}
        >
          <div className="grid grid-cols-1 gap-3 md:grid-cols-[minmax(0,1fr)_160px]">
            <Form.Item name="name" label="Name" rules={[{ required: true, message: 'Name is required' }]}>
              <Input placeholder="Technical Architecture Diagram" />
            </Form.Item>
            <Form.Item name="sortOrder" label="Sort Order" rules={[{ required: true, message: 'Sort order is required' }]}>
              <InputNumber className="w-full" min={1} precision={0} />
            </Form.Item>
          </div>

          <Form.Item name="key" label="Key" rules={[{ required: true, message: 'Key is required' }]}>
            <Input placeholder="technical_architecture_diagram" disabled={Boolean(editingItem)} />
          </Form.Item>

          <Form.Item name="purpose" label="Purpose" rules={[{ required: true, message: 'Purpose is required' }]}>
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>

          <Form.Item name="typicalContentsText" label="Typical Contents" rules={[{ required: true, message: 'At least one typical content is required' }]}>
            <Input.TextArea autoSize={{ minRows: 3, maxRows: 6 }} placeholder={'One item per line\nServices, modules, platforms'} />
          </Form.Item>

          <Form.Item name="isActive" label="Status" valuePropName="checked">
            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}