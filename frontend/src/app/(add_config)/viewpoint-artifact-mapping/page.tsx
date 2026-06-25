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
  Select,
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
import type { ArtifactCatalogItem } from '@/features/review/config/artifactCatalogConfig';
import { mergeArtifactCatalogConfig } from '@/features/review/config/artifactCatalogConfig';
import {
  type ViewpointArtifactMappingConfig,
  type ViewpointDefinition,
  emptyViewpointArtifactMappingConfig,
  mergeViewpointArtifactMappingConfig,
} from '@/features/review/config/viewpointArtifactMappingConfig';

type ConfigResponse = {
  configKey: string;
  version: number;
  config: Record<string, unknown>;
  changeNote?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  source: 'db' | 'default';
};

type ViewpointFormValues = {
  number: number;
  layer: string;
  viewpoint: string;
  concernKeys: string[];
  mandatoryArtifacts: string[];
  optionalArtifacts: string[];
  logicalPhysical: string;
  structureBehavior: string;
  purpose: string;
  example: string;
  primarySource: string;
  audience: string;
  notes: string;
  isActive: boolean;
  sortOrder: number;
};

const artifactShortLabels: Record<string, string> = {
  tech_diagram: 'Tech',
  app_collab: 'App',
  biz_diagram: 'Biz',
  data_compliance_diagram: 'Compliance',
  data_model: 'Model',
  data_asset_matrix: 'Asset',
  auth_flow: 'Auth',
  business_process: 'Process',
  data_pipeline: 'Pipeline',
  system_process_flow: 'System',
  resource_list: 'Resource',
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
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function sortViewpoints(items: ViewpointDefinition[]): ViewpointDefinition[] {
  return [...items].sort((left, right) => left.sortOrder - right.sortOrder || left.number - right.number);
}

function nextViewpointNumber(items: ViewpointDefinition[]): number {
  return Math.max(0, ...items.map((item) => item.number || 0)) + 1;
}

function toFormValues(item: ViewpointDefinition): ViewpointFormValues {
  return {
    number: item.number,
    layer: item.layer,
    viewpoint: item.viewpoint,
    concernKeys: item.concernKeys,
    mandatoryArtifacts: item.mandatoryArtifacts,
    optionalArtifacts: item.optionalArtifacts,
    logicalPhysical: item.logicalPhysical,
    structureBehavior: item.structureBehavior,
    purpose: item.purpose,
    example: item.example,
    primarySource: item.primarySource,
    audience: item.audience,
    notes: item.notes,
    isActive: item.isActive,
    sortOrder: item.sortOrder,
  };
}

function getArtifactFit(item: ViewpointDefinition, artifactKey: string): 'mandatory' | 'optional' | 'none' {
  if (item.mandatoryArtifacts.includes(artifactKey)) {
    return 'mandatory';
  }
  if (item.optionalArtifacts.includes(artifactKey)) {
    return 'optional';
  }
  return 'none';
}

function renderFit(value: 'mandatory' | 'optional' | 'none') {
  if (value === 'mandatory') {
    return <Tag color="green">Primary</Tag>;
  }
  if (value === 'optional') {
    return <Tag color="gold">Optional</Tag>;
  }
  return <span className="text-slate-300">-</span>;
}

export default function ViewpointArtifactMappingPage() {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm<ViewpointFormValues>();
  const isAdmin = hasRole('ea_admin');

  const [config, setConfig] = useState<ViewpointArtifactMappingConfig>(() => ({
    ...emptyViewpointArtifactMappingConfig,
    objectives: [],
    corePrinciples: [],
    relatedGuides: [],
    viewpoints: [],
  }));
  const [changeNote, setChangeNote] = useState('');
  const [searchText, setSearchText] = useState('');
  const [showInactive, setShowInactive] = useState(true);
  const [layerFilter, setLayerFilter] = useState<string | undefined>();
  const [artifactFilter, setArtifactFilter] = useState<string | undefined>();
  const [editingViewpoint, setEditingViewpoint] = useState<ViewpointDefinition | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['viewpointArtifactMappingConfig', 'default', 'adminPage'],
    queryFn: () => api.get<ConfigResponse>('/avdm/viewpoint-artifact-mapping-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const { data: artifactCatalogData } = useQuery({
    queryKey: ['architectureArtifactCatalogConfig', 'default', 'viewpointMappingPage'],
    queryFn: () => api.get<ConfigResponse>('/avdm/artifact-catalog-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const serverConfig = useMemo(() => mergeViewpointArtifactMappingConfig(data?.config || {}), [data?.config]);
  const artifactCatalog = useMemo(() => mergeArtifactCatalogConfig(artifactCatalogData?.config || {}), [artifactCatalogData?.config]);
  const artifactTypes = useMemo(() => artifactCatalog.artifactTypes.filter((item) => item.isActive), [artifactCatalog.artifactTypes]);
  const artifactNameByKey = useMemo(() => Object.fromEntries(artifactCatalog.artifactTypes.map((item) => [item.key, item.name])), [artifactCatalog.artifactTypes]);

  useEffect(() => {
    if (!data) {
      return;
    }
    setConfig(serverConfig);
  }, [data, serverConfig]);

  const layerOptions = useMemo(() => Array.from(new Set(config.viewpoints.map((item) => item.layer).filter(Boolean))), [config.viewpoints]);

  const filteredViewpoints = useMemo(() => {
    const needle = searchText.trim().toLowerCase();
    return sortViewpoints(config.viewpoints).filter((item) => {
      if (!showInactive && !item.isActive) {
        return false;
      }
      if (layerFilter && item.layer !== layerFilter) {
        return false;
      }
      if (artifactFilter) {
        const hasArtifact = item.mandatoryArtifacts.includes(artifactFilter) || item.optionalArtifacts.includes(artifactFilter);
        if (!hasArtifact) return false;
      }
      if (!needle) {
        return true;
      }
      return [
        item.layer,
        item.viewpoint,
        item.purpose,
        item.example,
        item.primarySource,
        item.audience,
        item.notes,
        ...item.mandatoryArtifacts.map((artifactKey) => artifactNameByKey[artifactKey] || artifactKey),
        ...item.optionalArtifacts.map((artifactKey) => artifactNameByKey[artifactKey] || artifactKey),
      ].some((value) => value.toLowerCase().includes(needle));
    });
  }, [artifactFilter, artifactNameByKey, config.viewpoints, layerFilter, searchText, showInactive]);

  const saveMutation = useMutation({
    mutationFn: async () => api.put<ConfigResponse>(
      '/avdm/viewpoint-artifact-mapping-config?configKey=default',
      {
        config: mergeViewpointArtifactMappingConfig(config),
        changeNote: changeNote || null,
        operator: user?.id || 'system',
      }
    ),
    onSuccess: () => {
      messageApi.success('Viewpoint and artifact mapping guide saved.');
      queryClient.invalidateQueries({ queryKey: ['viewpointArtifactMappingConfig'] });
      setChangeNote('');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save viewpoint and artifact mapping guide');
    },
  });

  const openEditor = (item?: ViewpointDefinition) => {
    const initial = item || {
      number: nextViewpointNumber(config.viewpoints),
      layer: '',
      viewpoint: '',
      concernKeys: [],
      mandatoryArtifacts: [],
      optionalArtifacts: [],
      logicalPhysical: 'L',
      structureBehavior: 'S',
      purpose: '',
      example: '',
      primarySource: '',
      audience: '',
      notes: '',
      isActive: true,
      sortOrder: nextViewpointNumber(config.viewpoints),
    } satisfies ViewpointDefinition;
    setEditingViewpoint(item || null);
    form.setFieldsValue(toFormValues(initial));
    setModalOpen(true);
  };

  const saveViewpoint = async () => {
    const values = await form.validateFields();
    const mandatoryArtifacts = values.mandatoryArtifacts || [];
    const optionalArtifacts = (values.optionalArtifacts || []).filter((artifactKey) => !mandatoryArtifacts.includes(artifactKey));

    const normalized: ViewpointDefinition = {
      number: Number(values.number),
      layer: values.layer.trim(),
      viewpoint: values.viewpoint.trim(),
      concernKeys: editingViewpoint?.concernKeys ?? [],
      mandatoryArtifacts,
      optionalArtifacts,
      logicalPhysical: values.logicalPhysical,
      structureBehavior: values.structureBehavior,
      purpose: values.purpose.trim(),
      example: values.example.trim(),
      primarySource: values.primarySource.trim(),
      audience: values.audience.trim(),
      notes: values.notes.trim(),
      isActive: values.isActive,
      sortOrder: Number(values.sortOrder) || Number(values.number),
    };

    setConfig((previous) => {
      const exists = previous.viewpoints.some((item) => item.number === normalized.number);
      return {
        ...previous,
        viewpoints: sortViewpoints(
          exists
            ? previous.viewpoints.map((item) => item.number === normalized.number ? normalized : item)
            : [...previous.viewpoints, normalized]
        ),
      };
    });

    setModalOpen(false);
    setEditingViewpoint(null);
  };

  const deleteViewpoint = (number: number) => {
    setConfig((previous) => ({
      ...previous,
      viewpoints: previous.viewpoints.filter((item) => item.number !== number),
    }));
  };

  const updateStatus = (number: number, isActive: boolean) => {
    setConfig((previous) => ({
      ...previous,
      viewpoints: previous.viewpoints.map((item) => item.number === number ? { ...item, isActive } : item),
    }));
  };

  const artifactColumns: ColumnsType<ViewpointDefinition> = artifactTypes.map((artifact: ArtifactCatalogItem) => ({
    title: artifactShortLabels[artifact.key] || artifact.name,
    key: artifact.key,
    width: 110,
    align: 'center',
    render: (_, record) => renderFit(getArtifactFit(record, artifact.key)),
  }));

  const columns: ColumnsType<ViewpointDefinition> = [
    {
      title: 'No',
      dataIndex: 'number',
      width: 72,
      fixed: 'left',
      sorter: (a, b) => a.number - b.number,
    },
    {
      title: 'Layer',
      dataIndex: 'layer',
      width: 220,
      fixed: 'left',
      render: (value: string) => <Tag>{value}</Tag>,
    },
    {
      title: 'Viewpoint',
      dataIndex: 'viewpoint',
      width: 250,
      fixed: 'left',
      render: (value: string, record) => (
        <div>
          <div className="font-medium text-slate-900">{value}</div>
          <div className="mt-1 text-xs text-slate-500">{record.logicalPhysical} / {record.structureBehavior}</div>
        </div>
      ),
    },
    ...artifactColumns,
    {
      title: 'Purpose',
      dataIndex: 'purpose',
      width: 320,
      ellipsis: true,
    },
    {
      title: 'Audience',
      dataIndex: 'audience',
      width: 180,
    },
    {
      title: 'Status',
      dataIndex: 'isActive',
      width: 120,
      render: (value: boolean, record) => (
        <Switch checked={value} checkedChildren="Active" unCheckedChildren="Inactive" onChange={(checked) => updateStatus(record.number, checked)} />
      ),
    },
    {
      title: 'Action',
      key: 'action',
      width: 112,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openEditor(record)} />
          <Popconfirm title="Delete viewpoint definition?" onConfirm={() => deleteViewpoint(record.number)}>
            <Button danger icon={<Trash2 className="h-4 w-4" />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const artifactOptions = artifactCatalog.artifactTypes.map((item) => ({ label: item.name, value: item.key }));
  if (!isAdmin) {
    return (
      <div className="p-6">
        {contextHolder}
        <Alert type="error" showIcon title="Access denied" description="Only EA Admin can maintain viewpoint and artifact mapping." />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {contextHolder}

      <section className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Typography.Title level={4} style={{ marginBottom: 4 }}>Viewpoint & Artifact Mapping</Typography.Title>
            <Typography.Text type="secondary">
              Maintain the canonical semantic mapping between architecture viewpoints and artifact types for the preparation-stage method baseline.
            </Typography.Text>
          </div>
          <Space wrap>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>
              Refresh
            </Button>
            <Button icon={<RotateCcw className="h-4 w-4" />} onClick={() => {
              setConfig(serverConfig);
              setChangeNote('');
            }}>
              Reset Server Config
            </Button>
            <Button icon={<Download className="h-4 w-4" />} onClick={() => downloadJson(
              `viewpoint-artifact-mapping-${new Date().toISOString().slice(0, 10)}.json`,
              mergeViewpointArtifactMappingConfig(config)
            )}>
              Export JSON
            </Button>
            <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
              Save Guide
            </Button>
          </Space>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(280px,1.4fr)_200px_minmax(260px,1fr)]">
        <Input value={config.guideName} onChange={(event) => setConfig((previous) => ({ ...previous, guideName: event.target.value }))} placeholder="Guide name" />
        <Input value={config.stage} disabled />
        <Input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="Change note for this version" />
      </div>

      <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(260px,1fr)_220px_180px_auto]">
                  <Input.Search
                    allowClear
                    value={searchText}
                    onChange={(event) => setSearchText(event.target.value)}
                    placeholder="Search layer, viewpoint, concern, purpose, source, audience"
                  />
                  <Select
                    allowClear
                    value={layerFilter}
                    onChange={setLayerFilter}
                    placeholder="Filter layer"
                    options={layerOptions.map((layer) => ({ label: layer, value: layer }))}
                  />
                  <Select
                    allowClear
                    style={{ width: 180 }}
                    value={artifactFilter}
                    onChange={setArtifactFilter}
                    placeholder="Filter artifact"
                    options={artifactTypes.map((a) => ({ label: a.name, value: a.key }))}
                  />
                  <div className="flex items-center gap-2 rounded border border-slate-200 bg-white px-3">
                    <Switch checked={showInactive} onChange={setShowInactive} />
                    <span className="text-sm text-slate-600">Show inactive</span>
                  </div>
                  <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openEditor()}>
                    Add Viewpoint
                  </Button>
                </div>

                <Table<ViewpointDefinition>
                  rowKey="number"
                  loading={isLoading}
                  columns={columns}
                  dataSource={filteredViewpoints}
                  pagination={{ pageSize: 12, showSizeChanger: true }}
                  scroll={{ x: 2600 }}
                />
              </div>

      <Modal
        title={editingViewpoint ? `Edit ${editingViewpoint.viewpoint}` : 'Add Viewpoint'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingViewpoint(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={920}
        destroyOnHidden
      >
        <Form<ViewpointFormValues> form={form} layout="vertical" onFinish={saveViewpoint} initialValues={{ isActive: true, logicalPhysical: 'L', structureBehavior: 'S' }}>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Form.Item name="number" label="No" rules={[{ required: true, message: 'No is required' }]}>
              <InputNumber className="w-full" min={1} precision={0} disabled={Boolean(editingViewpoint)} />
            </Form.Item>
            <Form.Item name="sortOrder" label="Sort Order" rules={[{ required: true, message: 'Sort order is required' }]}>
              <InputNumber className="w-full" min={1} precision={0} />
            </Form.Item>
            <Form.Item name="isActive" label="Status" valuePropName="checked">
              <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item name="layer" label="Layer" rules={[{ required: true, message: 'Layer is required' }]}>
              <Input placeholder="Business / Organization Layer" />
            </Form.Item>
            <Form.Item name="viewpoint" label="Viewpoint" rules={[{ required: true, message: 'Viewpoint is required' }]}>
              <Input placeholder="Business Capability View" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item name="logicalPhysical" label="L / P" rules={[{ required: true, message: 'L/P is required' }]}>
              <Select options={[{ label: 'L', value: 'L' }, { label: 'P', value: 'P' }, { label: 'L/P', value: 'L/P' }]} />
            </Form.Item>
            <Form.Item name="structureBehavior" label="S / B" rules={[{ required: true, message: 'S/B is required' }]}>
              <Select options={[{ label: 'S', value: 'S' }, { label: 'B', value: 'B' }, { label: 'S/B', value: 'S/B' }]} />
            </Form.Item>
          </div>

          <Form.Item name="mandatoryArtifacts" label="Primary Artifacts">
            <Select mode="multiple" options={artifactOptions} optionFilterProp="label" />
          </Form.Item>

          <Form.Item name="optionalArtifacts" label="Optional Artifacts">
            <Select mode="multiple" options={artifactOptions} optionFilterProp="label" />
          </Form.Item>

          <Form.Item name="purpose" label="Purpose / Focus" rules={[{ required: true, message: 'Purpose is required' }]}>
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>

          <Form.Item name="example" label="Example" rules={[{ required: true, message: 'Example is required' }]}>
            <Input placeholder="Order -> Approve -> Settle" />
          </Form.Item>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Form.Item name="primarySource" label="Primary Source">
              <Input placeholder="TOGAF / BIZBOK" />
            </Form.Item>
            <Form.Item name="audience" label="Audience">
              <Input placeholder="Product / Ops" />
            </Form.Item>
          </div>

          <Form.Item name="notes" label="Notes">
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}