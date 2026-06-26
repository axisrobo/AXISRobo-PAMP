'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Download, Edit3, Plus, RefreshCw, RotateCcw, Save, Trash2 } from 'lucide-react';

import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';
import {
  ConcernActivationCondition,
  ConcernActivationRule,
  ConcernMappingConfig,
  ConcernScoreMapping,
  QuestionConcernMapping,
  QuestionConfig,
  mergeConcernMappingConfig,
  mergeQuestionnaireConfig,
} from '@/features/review/config/questionnaireConfig';

type ConcernMappingConfigResponse = {
  configKey: string;
  version: number;
  config: Record<string, unknown>;
  changeNote?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  source: 'db' | 'default';
};

type QuestionnaireConfigResponse = ConcernMappingConfigResponse;

type PactConcern = {
  id: string;
  concernKey: string;
  concernName: string;
  layer: string;
  riskTags: string[];
  description: string;
  isActive: boolean;
};

type PactConcernCatalogResponse = {
  layers: string[];
  items: PactConcern[];
};

type EditableCondition = {
  source: string;
  operator: 'equals' | 'in' | 'notEquals';
  value: string;
};

type QuestionMappingFormValues = {
  questionId: number;
  answer: string;
  concernScores: ConcernScoreMapping[];
  hints?: string[];
};

type RuleFormValues = {
  id: string;
  description: string;
  all?: EditableCondition[];
  any?: EditableCondition[];
  concernScores: ConcernScoreMapping[];
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

function conditionToEditable(condition: ConcernActivationCondition): EditableCondition {
  if (Array.isArray(condition.in)) {
    return { source: condition.source, operator: 'in', value: condition.in.map(String).join(', ') };
  }
  if (condition.notEquals !== undefined) {
    return { source: condition.source, operator: 'notEquals', value: String(condition.notEquals) };
  }
  return { source: condition.source, operator: 'equals', value: condition.equals === undefined ? '' : String(condition.equals) };
}

function editableToCondition(condition: EditableCondition): ConcernActivationCondition | null {
  const source = condition.source?.trim();
  if (!source) return null;
  const rawValue = condition.value?.trim() || '';
  if (condition.operator === 'in') {
    return { source, in: rawValue.split(',').map((item) => item.trim()).filter(Boolean) };
  }
  if (condition.operator === 'notEquals') {
    return { source, notEquals: rawValue };
  }
  return { source, equals: rawValue };
}

function questionDisplayId(id: number): string {
  if (id >= 1 && id <= 25) return `A${id}`;
  if (id >= 26 && id <= 54) return `B${id - 25}`;
  if (id >= 55 && id <= 69) return `C${id - 54}`;
  return `Q${id}`;
}

const categoryIdPrefixMap: Record<string, string> = {
  business_change: 'BC', application_change: 'AC', data_change: 'DC', technology_change: 'TC',
  compliance_change: 'CC', other_change: 'OC', security_change: 'SEC',
  project_scale: 'PS', change_scale: 'CS', data_complexity: 'DCP', compliance_complexity: 'CCP',
  requirement_complexity: 'RCP', solution_complexity: 'SCP', technical_complexity: 'TCP', security_complexity: 'SECP',
  project_resource_and_size: 'PRS', technical_architecture_type: 'TAT', application_architecture_type: 'AAT',
  data_architecture_type: 'DAT', business_architecture_type: 'BAT', security_architecture_type: 'SAT',
};

function cleanConcernScores(items: ConcernScoreMapping[] | undefined): ConcernScoreMapping[] {
  const seen = new Set<string>();
  return (items || [])
    .filter((item) => {
      const concernKey = item?.concernKey?.trim();
      if (!concernKey || seen.has(concernKey)) {
        return false;
      }
      seen.add(concernKey);
      return true;
    })
    .map((item) => ({
      concernKey: item.concernKey.trim(),
      score: Number(item.score) || 0,
      note: item.note?.trim() || undefined,
    }));
}

function toRuleFormValues(rule?: ConcernActivationRule): RuleFormValues {
  return {
    id: rule?.id || '',
    description: rule?.description || '',
    all: (rule?.all || []).map(conditionToEditable),
    any: (rule?.any || []).map(conditionToEditable),
    concernScores: rule?.concernScores || [],
  };
}

function toQuestionFormValues(item?: QuestionConcernMapping): QuestionMappingFormValues {
  return {
    questionId: item?.questionId || 1,
    answer: item?.answer || 'Y',
    concernScores: item?.concernScores || [],
    hints: item?.hints || [],
  };
}

export default function ConcernMappingConfigPage() {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [questionMappingForm] = Form.useForm<QuestionMappingFormValues>();
  const [ruleForm] = Form.useForm<RuleFormValues>();
  const isAdmin = hasRole('ea_admin');

  const [config, setConfig] = useState<ConcernMappingConfig>(() => mergeConcernMappingConfig({}));
  const [changeNote, setChangeNote] = useState('');
  const [editingQuestionMapping, setEditingQuestionMapping] = useState<QuestionConcernMapping | null>(null);
  const [editingRule, setEditingRule] = useState<ConcernActivationRule | null>(null);
  const [questionMappingModalOpen, setQuestionMappingModalOpen] = useState(false);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  const selectedQuestionId = Form.useWatch('questionId', questionMappingForm);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['avdmConcernMappingConfig', 'default', 'adminPage'],
    queryFn: () => api.get<ConcernMappingConfigResponse>('/avdm/concern-mapping-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const { data: questionnaireData } = useQuery({
    queryKey: ['avdmQuestionnaireConfig', 'default', 'mappingPage'],
    queryFn: () => api.get<QuestionnaireConfigResponse>('/avdm/questionnaire-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const { data: concernCatalog } = useQuery({
    queryKey: ['pactConcernCatalog', 'mappingPage'],
    queryFn: () => api.get<PactConcernCatalogResponse>('/avdm/concerns', { includeInactive: true }),
    enabled: isAdmin,
  });

  const serverMappingConfig = useMemo(() => mergeConcernMappingConfig(data?.config || {}), [data?.config]);

  useEffect(() => {
    if (!data) return;
    setConfig(serverMappingConfig);
  }, [data, serverMappingConfig]);

  const questionConfig = useMemo(
    () => mergeQuestionnaireConfig(questionnaireData?.config || {}),
    [questionnaireData?.config]
  );

  const questionById = useMemo(() => {
    const catCounters = new Map<string, number>();
    return new Map(questionConfig.questionBank.map((item) => {
      const prefix = categoryIdPrefixMap[item.category] || item.category?.toUpperCase().substring(0, 3) || 'Q';
      const n = (catCounters.get(item.category) || 0) + 1;
      catCounters.set(item.category, n);
      return [item.id, { ...item, displayId: `${prefix}${n}` }];
    }));
  }, [questionConfig.questionBank]);
  const sortedMappings = useMemo(() =>
    [...config.questionConcernMappings].sort((a, b) => a.questionId - b.questionId),
  [config.questionConcernMappings]);

  const concernByKey = useMemo(() => new Map((concernCatalog?.items || []).map((item) => [item.concernKey, item])), [concernCatalog?.items]);
  const selectedQuestion = useMemo(() => questionById.get(Number(selectedQuestionId)), [questionById, selectedQuestionId]);

  const selectedQuestionAnswerOptions = useMemo(() => {
    if (!selectedQuestion) {
      return [];
    }

    if (selectedQuestion.optionsSource) {
      const optionSet = questionConfig.optionSets.find((item) => item.key === selectedQuestion.optionsSource);
      const sourceOptions = optionSet?.options || questionConfig[selectedQuestion.optionsSource as keyof typeof questionConfig] as unknown[];
      if (Array.isArray(sourceOptions)) {
        return sourceOptions
          .filter((item: unknown): item is { label: string; value: string } => {
            if (!item || typeof item !== 'object') {
              return false;
            }
            const candidate = item as { label?: unknown; value?: unknown };
            return typeof candidate.label === 'string' && typeof candidate.value === 'string';
          })
          .map((item) => ({ label: item.label, value: item.value }));
      }
    }

    if (selectedQuestion.options?.length) {
      return selectedQuestion.options.map((item) => ({ label: item.label, value: item.value }));
    }

    return [];
  }, [questionConfig, selectedQuestion]);

  const questionOptions = useMemo(() => questionConfig.questionBank.map((item) => {
    const q = questionById.get(item.id) as (QuestionConfig & { displayId: string }) | undefined;
    return {
      label: `${q?.displayId || questionDisplayId(item.id)}. ${item.text}`,
      value: item.id,
    };
  }), [questionConfig.questionBank, questionById]);

  const concernOptions = useMemo(() => {
    const fromCatalog = (concernCatalog?.items || []).map((item) => ({
      label: `${item.concernKey} - ${item.concernName}`,
      value: item.concernKey,
    }));
    if (fromCatalog.length > 0) return fromCatalog;
    const keys = new Set<string>();
    config.questionConcernMappings.forEach((mapping) => mapping.concernScores.forEach((item) => keys.add(item.concernKey)));
    config.concernActivationRules.forEach((rule) => rule.concernScores.forEach((item) => keys.add(item.concernKey)));
    return Array.from(keys).sort().map((key) => ({ label: key, value: key }));
  }, [concernCatalog?.items, config]);

  const saveMutation = useMutation({
    mutationFn: async () => api.put<ConcernMappingConfigResponse>(
      '/avdm/concern-mapping-config?configKey=default',
      {
        config: mergeConcernMappingConfig(config),
        changeNote: changeNote || null,
        operator: user?.id || 'system',
      }
    ),
    onSuccess: () => {
      messageApi.success('Concern mapping config saved. New version published.');
      queryClient.invalidateQueries({ queryKey: ['avdmConcernMappingConfig', 'default'] });
      queryClient.invalidateQueries({ queryKey: ['avdmConcernMappingConfig', 'default', 'adminPage'] });
      setChangeNote('');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save concern mapping config');
    },
  });

  const openQuestionMappingEditor = (item?: QuestionConcernMapping) => {
    setEditingQuestionMapping(item || null);
    questionMappingForm.setFieldsValue(toQuestionFormValues(item));
    setQuestionMappingModalOpen(true);
  };

  const openRuleEditor = (rule?: ConcernActivationRule) => {
    setEditingRule(rule || null);
    ruleForm.setFieldsValue(toRuleFormValues(rule));
    setRuleModalOpen(true);
  };

  const saveQuestionMapping = async () => {
    const values = await questionMappingForm.validateFields();
    const normalized: QuestionConcernMapping = {
      questionId: Number(values.questionId),
      answer: values.answer || 'Y',
      concernScores: cleanConcernScores(values.concernScores),
      hints: values.hints?.filter(Boolean),
    };
    if (normalized.concernScores.length === 0) {
      messageApi.warning('Add at least one concern score.');
      return;
    }
    setConfig((previous) => {
      const sameKey = (item: QuestionConcernMapping) => item.questionId === normalized.questionId && item.answer === normalized.answer;
      const exists = previous.questionConcernMappings.some(sameKey);
      return {
        ...previous,
        questionConcernMappings: exists
          ? previous.questionConcernMappings.map((item) => sameKey(item) ? normalized : item)
          : [...previous.questionConcernMappings, normalized].sort((a, b) => a.questionId - b.questionId),
      };
    });
    setQuestionMappingModalOpen(false);
  };

  const saveRule = async () => {
    const values = await ruleForm.validateFields();
    const all = (values.all || []).map(editableToCondition).filter(Boolean) as ConcernActivationCondition[];
    const any = (values.any || []).map(editableToCondition).filter(Boolean) as ConcernActivationCondition[];
    const normalized: ConcernActivationRule = {
      id: values.id.trim(),
      description: values.description.trim(),
      all,
      any,
      concernScores: cleanConcernScores(values.concernScores),
    };
    if (!normalized.id || normalized.concernScores.length === 0) {
      messageApi.warning('Rule ID and at least one concern score are required.');
      return;
    }
    setConfig((previous) => {
      const exists = previous.concernActivationRules.some((item) => item.id === normalized.id);
      return {
        ...previous,
        concernActivationRules: exists
          ? previous.concernActivationRules.map((item) => item.id === normalized.id ? normalized : item)
          : [...previous.concernActivationRules, normalized],
      };
    });
    setRuleModalOpen(false);
  };

  const deleteQuestionMapping = (record: QuestionConcernMapping) => {
    setConfig((previous) => ({
      ...previous,
      questionConcernMappings: previous.questionConcernMappings.filter((item) => !(item.questionId === record.questionId && item.answer === record.answer)),
    }));
  };

  const deleteRule = (id: string) => {
    setConfig((previous) => ({
      ...previous,
      concernActivationRules: previous.concernActivationRules.filter((item) => item.id !== id),
    }));
  };

  const renderConcernScores = (scores: ConcernScoreMapping[]) => (
    <Space size={[4, 4]} wrap>
      {(scores || []).map((item) => {
        const concern = concernByKey.get(item.concernKey);
        return (
          <Tag key={`${item.concernKey}-${item.score}`} color="blue">
            {item.concernKey} +{item.score}{concern ? ` ${concern.concernName}` : ''}
          </Tag>
        );
      })}
    </Space>
  );

  const questionMappingColumns: ColumnsType<QuestionConcernMapping> = [
    {
      title: 'Question',
      dataIndex: 'questionId',
      width: 380,
      render: (questionId: number) => {
        const question = questionById.get(questionId) as (QuestionConfig & { displayId: string }) | undefined;
        return (
          <div>
            <Typography.Text strong>{question?.displayId || questionDisplayId(questionId)}</Typography.Text>
            <div className="mt-1 text-xs text-slate-500">{question?.text || 'Question not found'}</div>
          </div>
        );
      },
    },
    { title: 'Answer', dataIndex: 'answer', width: 100, render: (value) => <Tag>{value}</Tag> },
    { title: 'Concern Scores', dataIndex: 'concernScores', render: renderConcernScores },
    {
      title: 'Hints',
      dataIndex: 'hints',
      width: 260,
      render: (hints?: string[]) => <Space size={[4, 4]} wrap>{(hints || []).map((hint) => <Tag key={hint}>{hint}</Tag>)}</Space>,
    },
    {
      title: 'Action',
      key: 'action',
      width: 168,
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openQuestionMappingEditor(record)} />
          <Popconfirm title="Delete mapping?" onConfirm={() => deleteQuestionMapping(record)}>
            <Button danger icon={<Trash2 className="h-4 w-4" />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const ruleColumns: ColumnsType<ConcernActivationRule> = [
    { title: 'Rule ID', dataIndex: 'id', width: 260, render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    { title: 'Description', dataIndex: 'description', ellipsis: true },
    { title: 'ALL', dataIndex: 'all', width: 88, render: (value?: unknown[]) => <Tag>{value?.length || 0}</Tag> },
    { title: 'ANY', dataIndex: 'any', width: 88, render: (value?: unknown[]) => <Tag>{value?.length || 0}</Tag> },
    { title: 'Concern Scores', dataIndex: 'concernScores', width: 360, render: renderConcernScores },
    {
      title: 'Action',
      key: 'action',
      width: 168,
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openRuleEditor(record)} />
          <Popconfirm title="Delete rule?" onConfirm={() => deleteRule(record.id)}>
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
        <Alert type="error" showIcon title="Access denied" description="Only EA Admin can maintain questionnaire-to-concern mapping." />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {contextHolder}

      <section className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Typography.Title level={4} style={{ marginBottom: 4 }}>Questionnaire & Concern Mapping</Typography.Title>
            <Typography.Text type="secondary">Maintain answer mappings and activation rules (single-signal and combination) with additive PACT concern risk scores.</Typography.Text>
          </div>
          <Space wrap>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
            <Button icon={<Download className="h-4 w-4" />} onClick={() => downloadJson(`avdm-concern-mapping-config-${new Date().toISOString().slice(0, 10)}.json`, mergeConcernMappingConfig(config))}>Export JSON</Button>
            <Button icon={<RotateCcw className="h-4 w-4" />} onClick={() => setConfig(serverMappingConfig)}>Reset Server Config</Button>
            <Button type="primary" icon={<Save className="h-4 w-4" />} onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>Save New Version</Button>
          </Space>
        </div>
      </section>

      <Card loading={isLoading}>
        <div className="mb-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-4">
          <div><span className="text-slate-500">Config Key: </span><span className="font-medium">{data?.configKey || 'default'}</span></div>
          <div><span className="text-slate-500">Version: </span><span className="font-medium">{data?.version || 1}</span></div>
          <div><span className="text-slate-500">Source: </span><span className="font-medium">{data?.source || 'default'}</span></div>
          <div><span className="text-slate-500">Updated By: </span><span className="font-medium">{data?.updatedBy || '-'}</span></div>
        </div>
        <div className="mb-4">
          <div className="mb-1 text-sm font-medium">Change Note</div>
          <Input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="e.g. 调整外部访问场景 SCR7 叠加分" maxLength={200} />
        </div>

        <Tabs
          items={[
            {
              key: 'questionMappings',
              label: `Question Mappings (${config.questionConcernMappings.length})`,
              children: (
                <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                  <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openQuestionMappingEditor()}>Add Question Mapping</Button>
                  <Table rowKey={(record) => `${record.questionId}-${record.answer}`} columns={questionMappingColumns} dataSource={sortedMappings} pagination={{ pageSize: 8 }} />
                </Space>
              ),
            },
            {
              key: 'rules',
              label: `Activation Rules (${config.concernActivationRules.length})`,
              children: (
                <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                  <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openRuleEditor()}>Add Rule</Button>
                  <Table rowKey="id" columns={ruleColumns} dataSource={config.concernActivationRules} pagination={{ pageSize: 8 }} />
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal title={editingQuestionMapping ? 'Edit Question Mapping' : 'Add Question Mapping'} open={questionMappingModalOpen} onCancel={() => setQuestionMappingModalOpen(false)} onOk={saveQuestionMapping} width={860} destroyOnHidden>
        <Form form={questionMappingForm} layout="vertical">
          <Form.Item name="questionId" label="Question" rules={[{ required: true }]}>
            <Select disabled={!!editingQuestionMapping} options={questionOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          {selectedQuestionAnswerOptions.length > 0 ? (
            <Form.Item name="answer" label="Answer" rules={[{ required: true }]}>
              <Select disabled={!!editingQuestionMapping} options={selectedQuestionAnswerOptions} />
            </Form.Item>
          ) : (
            <Form.Item
              name="answer"
              label="Answer"
              rules={[{ required: true }]}
              extra="This question uses free text input. Mapping matches the exact saved answer value."
            >
              <Input disabled={!!editingQuestionMapping} placeholder="Enter the exact answer value to match" />
            </Form.Item>
          )}
          <Form.Item name="hints" label="Hints">
            <Select mode="tags" tokenSeparators={[',']} placeholder="Business capability, Security boundary" />
          </Form.Item>
          <Typography.Text strong>Concern Scores</Typography.Text>
          <Form.List name="concernScores">
            {(fields, { add, remove }) => (
              <Space orientation="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ width: '100%' }}>
                    <Form.Item {...field} name={[field.name, 'concernKey']} rules={[{ required: true }]} style={{ width: 420 }}>
                      <Select options={concernOptions} showSearch optionFilterProp="label" placeholder="Concern" />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'score']} rules={[{ required: true }]} style={{ width: 140 }}>
                      <InputNumber min={0} max={100} placeholder="Score" style={{ width: '100%' }} />
                    </Form.Item>
                    <Button danger icon={<Trash2 className="h-4 w-4" />} onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button icon={<Plus className="h-4 w-4" />} onClick={() => add({ concernKey: undefined, score: 8 })}>Add Concern Score</Button>
              </Space>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal title={editingRule ? 'Edit Activation Rule' : 'Add Activation Rule'} open={ruleModalOpen} onCancel={() => setRuleModalOpen(false)} onOk={saveRule} width={920} destroyOnHidden>
        <Form form={ruleForm} layout="vertical">
          <Form.Item name="id" label="Rule ID" rules={[{ required: true }]}>
            <Input disabled={!!editingRule} placeholder="identity-and-authorization-combination" />
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>

          <Typography.Text strong>ALL Conditions</Typography.Text>
          <Form.List name="all">
            {(fields, { add, remove }) => (
              <Space orientation="vertical" size={8} style={{ width: '100%', marginTop: 8, marginBottom: 16 }}>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ width: '100%' }}>
                    <Form.Item {...field} name={[field.name, 'source']} style={{ width: 360 }}>
                      <Input placeholder="question.7.answer" />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'operator']} style={{ width: 140 }}>
                      <Select options={[{ label: 'equals', value: 'equals' }, { label: 'in', value: 'in' }, { label: 'notEquals', value: 'notEquals' }]} />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'value']} style={{ width: 260 }}>
                      <Input placeholder="Y or Yes, No" />
                    </Form.Item>
                    <Button danger icon={<Trash2 className="h-4 w-4" />} onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button icon={<Plus className="h-4 w-4" />} onClick={() => add({ source: '', operator: 'equals', value: '' })}>Add ALL Condition</Button>
              </Space>
            )}
          </Form.List>

          <Typography.Text strong>ANY Conditions</Typography.Text>
          <Form.List name="any">
            {(fields, { add, remove }) => (
              <Space orientation="vertical" size={8} style={{ width: '100%', marginTop: 8, marginBottom: 16 }}>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ width: '100%' }}>
                    <Form.Item {...field} name={[field.name, 'source']} style={{ width: 360 }}>
                      <Input placeholder="question.20.answer" />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'operator']} style={{ width: 140 }}>
                      <Select options={[{ label: 'equals', value: 'equals' }, { label: 'in', value: 'in' }, { label: 'notEquals', value: 'notEquals' }]} />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'value']} style={{ width: 260 }}>
                      <Input placeholder="Y or Yes, No" />
                    </Form.Item>
                    <Button danger icon={<Trash2 className="h-4 w-4" />} onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button icon={<Plus className="h-4 w-4" />} onClick={() => add({ source: '', operator: 'equals', value: '' })}>Add ANY Condition</Button>
              </Space>
            )}
          </Form.List>

          <Typography.Text strong>Concern Scores</Typography.Text>
          <Form.List name="concernScores">
            {(fields, { add, remove }) => (
              <Space orientation="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ width: '100%' }}>
                    <Form.Item {...field} name={[field.name, 'concernKey']} rules={[{ required: true }]} style={{ width: 420 }}>
                      <Select options={concernOptions} showSearch optionFilterProp="label" placeholder="Concern" />
                    </Form.Item>
                    <Form.Item {...field} name={[field.name, 'score']} rules={[{ required: true }]} style={{ width: 140 }}>
                      <InputNumber min={0} max={100} placeholder="Score" style={{ width: '100%' }} />
                    </Form.Item>
                    <Button danger icon={<Trash2 className="h-4 w-4" />} onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button icon={<Plus className="h-4 w-4" />} onClick={() => add({ concernKey: undefined, score: 10 })}>Add Concern Score</Button>
              </Space>
            )}
          </Form.List>
        </Form>
      </Modal>
    </div>
  );
}
