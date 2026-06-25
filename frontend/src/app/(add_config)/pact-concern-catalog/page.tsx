'use client';

import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Download, Edit3, Plus, RefreshCw } from 'lucide-react';

import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';

const { TextArea } = Input;

type PactConcern = {
  id: string;
  concernKey: string;
  concernName: string;
  layer: string;
  riskTags: string[];
  description: string;
  isActive: boolean;
  updatedAt?: string | null;
  updatedBy?: string | null;
};

type PactConcernCatalogResponse = {
  layers: string[];
  items: PactConcern[];
};

type PactConcernCatalogExportResponse = PactConcernCatalogResponse & {
  catalogName: string;
  version: number;
  exportedAt: string;
  includeInactive: boolean;
  total: number;
};

type PactConcernFormValues = {
  concernKey: string;
  concernName: string;
  layer: string;
  riskTagsText: string;
  description: string;
  isActive: boolean;
};

const splitRiskTags = (value: string) => value
  .split(/[,\n]/)
  .map((item) => item.trim())
  .filter(Boolean);

const toFormValues = (item?: PactConcern): PactConcernFormValues => ({
  concernKey: item?.concernKey || '',
  concernName: item?.concernName || '',
  layer: item?.layer || '',
  riskTagsText: item?.riskTags?.join(', ') || '',
  description: item?.description || '',
  isActive: item?.isActive ?? true,
});

export default function PactConcernCatalogPage() {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm<PactConcernFormValues>();
  const isAdmin = hasRole('ea_admin');

  const [searchText, setSearchText] = useState('');
  const [layerFilter, setLayerFilter] = useState<string | undefined>();
  const [includeInactive, setIncludeInactive] = useState(true);
  const [editingItem, setEditingItem] = useState<PactConcern | undefined>();
  const [modalOpen, setModalOpen] = useState(false);

  const queryParams = useMemo(() => ({ layer: layerFilter, includeInactive }), [layerFilter, includeInactive]);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pactConcernCatalog', queryParams],
    queryFn: () => api.get<PactConcernCatalogResponse>('/avdm/concerns', queryParams),
    enabled: isAdmin,
  });

  const filteredItems = useMemo(() => {
    const needle = searchText.trim().toLowerCase();
    const items = data?.items || [];
    if (!needle) return items;
    return items.filter((item) => [
      item.concernKey,
      item.concernName,
      item.layer,
      item.description,
      ...(item.riskTags || []),
    ].some((value) => value?.toLowerCase().includes(needle)));
  }, [data?.items, searchText]);

  const saveMutation = useMutation({
    mutationFn: (values: PactConcernFormValues) => api.put<PactConcern>('/avdm/concerns', {
      concernKey: values.concernKey.trim(),
      concernName: values.concernName.trim(),
      layer: values.layer.trim(),
      riskTags: splitRiskTags(values.riskTagsText),
      description: values.description?.trim() || '',
      isActive: values.isActive,
      operator: user?.id || 'system',
    }),
    onSuccess: () => {
      messageApi.success('PACT concern saved.');
      queryClient.invalidateQueries({ queryKey: ['pactConcernCatalog'] });
      setModalOpen(false);
      setEditingItem(undefined);
      form.resetFields();
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save PACT concern');
    },
  });

  const exportMutation = useMutation({
    mutationFn: () => api.get<PactConcernCatalogExportResponse>('/avdm/concerns/export', { includeInactive: true }),
    onSuccess: (payload) => {
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `pact-concern-catalog-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      messageApi.success('PACT concern catalog exported.');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to export PACT concern catalog');
    },
  });

  const openEditor = (item?: PactConcern) => {
    setEditingItem(item);
    form.setFieldsValue(toFormValues(item));
    setModalOpen(true);
  };

  const toggleStatus = (item: PactConcern, isActive: boolean) => {
    saveMutation.mutate({
      concernKey: item.concernKey,
      concernName: item.concernName,
      layer: item.layer,
      riskTagsText: item.riskTags.join(', '),
      description: item.description,
      isActive,
    });
  };

  const columns: ColumnsType<PactConcern> = [
    {
      title: 'No.',
      dataIndex: 'concernKey',
      width: 92,
      sorter: (a, b) => a.concernKey.localeCompare(b.concernKey),
      render: (value: string) => <Typography.Text strong>{value}</Typography.Text>,
    },
    {
      title: 'Category',
      dataIndex: 'layer',
      width: 230,
      filters: (data?.layers || []).map((layer) => ({ text: layer, value: layer })),
      onFilter: (value, record) => record.layer === value,
    },
    {
      title: 'Concern',
      dataIndex: 'concernName',
      width: 260,
      render: (value: string, record) => (
        <div>
          <div className="font-medium text-slate-900">{value}</div>
          <div className="mt-1 text-xs text-slate-500">{record.updatedBy || 'system'}</div>
        </div>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: 'Tags',
      dataIndex: 'riskTags',
      width: 220,
      render: (tags: string[]) => (
        <Space size={[4, 4]} wrap>
          {(tags || []).slice(0, 4).map((tag) => <Tag key={tag}>{tag}</Tag>)}
          {(tags || []).length > 4 && <Tag>+{tags.length - 4}</Tag>}
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
          loading={saveMutation.isPending && saveMutation.variables?.concernKey === record.concernKey}
          onChange={(checked) => toggleStatus(record, checked)}
        />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 104,
      render: (_, record) => (
        <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openEditor(record)}>
          Edit
        </Button>
      ),
    },
  ];

  if (!isAdmin) {
    return (
      <div className="p-6">
        {contextHolder}
        <Alert type="error" showIcon title="Access denied" description="Only EA Admin can maintain PACT concern catalog." />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {contextHolder}

      <section className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Typography.Title level={4} style={{ marginBottom: 4 }}>Concern Catalog</Typography.Title>
            <Typography.Text type="secondary">Manage the 52 concern master records independently from questionnaire mapping rules.</Typography.Text>
          </div>
          <Space wrap>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>
              Refresh
            </Button>
            <Button icon={<Download className="h-4 w-4" />} onClick={() => exportMutation.mutate()} loading={exportMutation.isPending}>
              Export JSON
            </Button>
            <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openEditor()}>
              Add Concern
            </Button>
          </Space>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(260px,1fr)_280px_180px]">
        <Input.Search
          allowClear
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Search number, concern, category, tag"
        />
        <Select
          allowClear
          value={layerFilter}
          onChange={setLayerFilter}
          placeholder="Filter category"
          options={(data?.layers || []).map((layer) => ({ label: layer, value: layer }))}
        />
        <div className="flex items-center gap-2 rounded border border-slate-200 bg-white px-3">
          <Switch checked={includeInactive} onChange={setIncludeInactive} />
          <span className="text-sm text-slate-600">Show inactive</span>
        </div>
      </div>

      <Table<PactConcern>
        rowKey="concernKey"
        loading={isLoading}
        columns={columns}
        dataSource={filteredItems}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingItem ? `Edit ${editingItem.concernKey}` : 'Add PACT Concern'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingItem(undefined);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={saveMutation.isPending}
        destroyOnHidden
        width={720}
      >
        <Form<PactConcernFormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => saveMutation.mutate(values)}
          initialValues={{ isActive: true }}
        >
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item name="concernKey" label="Number" rules={[{ required: true, message: 'Number is required' }]}>
              <Input placeholder="B1" disabled={Boolean(editingItem)} />
            </Form.Item>
            <Form.Item name="layer" label="Category" rules={[{ required: true, message: 'Category is required' }]}>
              <Select
                showSearch
                placeholder="Select or type category"
                options={(data?.layers || []).map((layer) => ({ label: layer, value: layer }))}
              />
            </Form.Item>
          </div>
          <Form.Item name="concernName" label="Name" rules={[{ required: true, message: 'Name is required' }]}>
            <Input placeholder="Business Capability View" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <TextArea autoSize={{ minRows: 3, maxRows: 6 }} />
          </Form.Item>
          <Form.Item name="riskTagsText" label="Tags">
            <TextArea autoSize={{ minRows: 2, maxRows: 4 }} placeholder="B1, business, capability, scope" />
          </Form.Item>
          <Form.Item name="isActive" label="Status" valuePropName="checked">
            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
