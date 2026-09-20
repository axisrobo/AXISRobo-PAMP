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
  Select,
  Space,
  Switch,
  Typography,
  message,
} from 'antd';
import { RefreshCw, RotateCcw, Save } from 'lucide-react';

import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';

type ClassificationPolicy = {
  mandatoryThreshold: number;
  recommendedThreshold: number;
  complexityCoefficient: number;
  maxMandatoryCount: number | null;
  maxMandatoryRatio: number | null;
  topNPriorityBudget: number | null;
  tieBreakStrategy: 'score_then_key' | 'catalog_order' | 'stable_input';
};

type PolicyResponse = {
  configKey: string;
  version: number;
  config: { policy?: ClassificationPolicy };
  changeNote?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  source: 'db' | 'default';
};

const DEFAULTS: ClassificationPolicy = {
  mandatoryThreshold: 0.90,
  recommendedThreshold: 0.50,
  complexityCoefficient: 0.15,
  maxMandatoryCount: null,
  maxMandatoryRatio: null,
  topNPriorityBudget: null,
  tieBreakStrategy: 'score_then_key',
};

const TIE_BREAK_OPTIONS = [
  { label: 'Score, then concern key', value: 'score_then_key' },
  { label: 'Score, then catalog order', value: 'catalog_order' },
  { label: 'Score, then input order', value: 'stable_input' },
];

type FormValues = {
  mandatoryThreshold: number;
  recommendedThreshold: number;
  complexityCoefficient: number;
  limitMandatory: boolean;
  maxMandatoryCount: number | null;
  maxMandatoryRatio: number | null;
  enableTopN: boolean;
  topNPriorityBudget: number | null;
  tieBreakStrategy: ClassificationPolicy['tieBreakStrategy'];
};

export default function ClassificationPolicyPage() {
  const { hasRole, user } = useAuth();
  const isAdmin = hasRole('ea_admin');
  const [messageApi, contextHolder] = message.useMessage();
  const queryClient = useQueryClient();
  const [form] = Form.useForm<FormValues>();
  const [changeNote, setChangeNote] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['avdmClassificationPolicy', 'default'],
    queryFn: () => api.get<PolicyResponse>('/avdm/classification-policy', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const policy = useMemo<ClassificationPolicy>(
    () => ({ ...DEFAULTS, ...(data?.config?.policy || {}) }),
    [data?.config]
  );

  useEffect(() => {
    form.setFieldsValue({
      mandatoryThreshold: policy.mandatoryThreshold,
      recommendedThreshold: policy.recommendedThreshold,
      complexityCoefficient: policy.complexityCoefficient,
      limitMandatory: policy.maxMandatoryCount !== null || policy.maxMandatoryRatio !== null,
      maxMandatoryCount: policy.maxMandatoryCount,
      maxMandatoryRatio: policy.maxMandatoryRatio,
      enableTopN: policy.topNPriorityBudget !== null,
      topNPriorityBudget: policy.topNPriorityBudget,
      tieBreakStrategy: policy.tieBreakStrategy,
    });
  }, [policy, form]);

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const next: ClassificationPolicy = {
        mandatoryThreshold: values.mandatoryThreshold,
        recommendedThreshold: values.recommendedThreshold,
        complexityCoefficient: values.complexityCoefficient,
        maxMandatoryCount: values.limitMandatory ? values.maxMandatoryCount ?? null : null,
        maxMandatoryRatio: values.limitMandatory ? values.maxMandatoryRatio ?? null : null,
        topNPriorityBudget: values.enableTopN ? values.topNPriorityBudget ?? null : null,
        tieBreakStrategy: values.tieBreakStrategy,
      };
      return api.put<PolicyResponse>('/avdm/classification-policy?configKey=default', {
        config: { policy: next },
        changeNote: changeNote || null,
        operator: user?.id || 'system',
      });
    },
    onSuccess: () => {
      messageApi.success('Classification policy saved.');
      queryClient.invalidateQueries({ queryKey: ['avdmClassificationPolicy', 'default'] });
      setChangeNote('');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save classification policy');
    },
  });

  return (
    <div className="p-6">
      {contextHolder}
      <Space orientation="vertical" size="large" style={{ width: '100%' }}>
        <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 0 }}>
              AVDM Classification Policy
            </Typography.Title>
            <Typography.Text type="secondary">
              Configure thresholds, the complexity coefficient, Mandatory caps, the top-N priority budget, and tie-breaking.
            </Typography.Text>
          </div>
          <Space>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>
              Reload
            </Button>
            <Button
              icon={<RotateCcw className="h-4 w-4" />}
              onClick={() => form.setFieldsValue({ ...DEFAULTS, limitMandatory: false, enableTopN: false })}
            >
              Reset to defaults
            </Button>
          </Space>
        </Space>

        {data?.source === 'default' && (
          <Alert type="info" showIcon title="Using built-in defaults until the policy is saved." />
        )}

        <Card>
          <Form<FormValues>
            form={form}
            layout="vertical"
            initialValues={{ ...DEFAULTS, limitMandatory: false, enableTopN: false }}
            onFinish={(values) => saveMutation.mutate(values)}
          >
            <Space size="large" wrap>
              <Form.Item
                label="Mandatory threshold"
                name="mandatoryThreshold"
                rules={[{ required: true }]}
                tooltip="Score at or above this value is Mandatory."
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: 160 }} />
              </Form.Item>
              <Form.Item
                label="Recommended threshold"
                name="recommendedThreshold"
                rules={[{ required: true }]}
                tooltip="Score at or above this value (below Mandatory) is Recommended."
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: 160 }} />
              </Form.Item>
              <Form.Item
                label="Complexity coefficient"
                name="complexityCoefficient"
                rules={[{ required: true }]}
                tooltip="Maximum score added by project complexity (0-1)."
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: 160 }} />
              </Form.Item>
              <Form.Item label="Tie-break strategy" name="tieBreakStrategy" rules={[{ required: true }]}>
                <Select options={TIE_BREAK_OPTIONS} style={{ width: 240 }} />
              </Form.Item>
            </Space>

            <Space size="large" align="start" wrap>
              <Form.Item label="Limit number of Mandatory concerns" name="limitMandatory" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item label="Max Mandatory count" name="maxMandatoryCount">
                <InputNumber min={0} step={1} style={{ width: 160 }} placeholder="optional" />
              </Form.Item>
              <Form.Item label="Max Mandatory ratio (0-1)" name="maxMandatoryRatio">
                <InputNumber min={0} max={1} step={0.01} style={{ width: 160 }} placeholder="optional" />
              </Form.Item>
            </Space>

            <Space size="large" align="start" wrap>
              <Form.Item label="Enable top-N priority budget" name="enableTopN" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item label="Top-N budget" name="topNPriorityBudget">
                <InputNumber min={1} step={1} style={{ width: 160 }} placeholder="optional" />
              </Form.Item>
            </Space>

            <Form.Item label="Change note">
              <Input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="Describe this policy change" />
            </Form.Item>

            <Space>
              <Button type="primary" htmlType="submit" icon={<Save className="h-4 w-4" />} loading={saveMutation.isPending}>
                Save policy
              </Button>
              <Typography.Text type="secondary">
                Version {data?.version ?? 1}
                {data?.updatedBy ? ` · last updated by ${data.updatedBy}` : ''}
              </Typography.Text>
            </Space>
          </Form>
        </Card>
      </Space>
    </div>
  );
}
