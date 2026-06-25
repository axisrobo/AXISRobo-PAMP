'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
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
  AnswerOptionSetConfig,
  AssessmentMatrixSection,
  CategoryConfig,
  Option,
  ProjectTypeArtifactStatus,
  ProjectTypeGuide,
  ProjectTypeProfile,
  QuestionControl,
  QuestionConfig,
  QuestionnaireCategoryKey,
  QuestionnaireCategoryGroupKey,
  QuestionnaireConfig,
  QuestionnaireSection,
  mergeQuestionnaireConfig,
} from '@/features/review/config/questionnaireConfig';

type QuestionnaireConfigResponse = {
  configKey: string;
  version: number;
  config: Record<string, unknown>;
  changeNote?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  source: 'db' | 'default';
};

type OptionSectionKey = Exclude<
  keyof QuestionnaireConfig,
  'answerTypes' | 'optionSets' | 'questionnaireCategories' | 'questionBank' | 'projectTypeGuide' | 'questionnaireSections' | 'assessmentMatrices' | 'projectTypeProfiles'
>;

type CategoryFormValues = CategoryConfig;
type QuestionFormValues = QuestionConfig;
type OptionFormValues = Option;
type OptionSetFormValues = Pick<AnswerOptionSetConfig, 'key' | 'name' | 'description'>;
type ManagedQuestionRow = {
  rowKey: string;
  displayId: string;
  category: string;
  text: string;
  control: string;
  optionsSummary: string;
  designIntent?: string;
  editable: boolean;
  sourceTab?: string;
  questionId?: number;
};

type CategoryGroupSection = {
  label: string;
  value?: QuestionnaireCategoryGroupKey;
  items: CategoryConfig[];
};

const categoryIdPrefixMap: Record<string, string> = {
  business_change: 'BC',
  application_change: 'AC',
  data_change: 'DC',
  technology_change: 'TC',
  compliance_change: 'CC',
  other_change: 'OC',
  security_change: 'SEC',
  project_scale: 'PS',
  change_scale: 'CS',
  data_complexity: 'DCP',
  compliance_complexity: 'CCP',
  requirement_complexity: 'RCP',
  solution_complexity: 'SCP',
  technical_complexity: 'TCP',
  security_complexity: 'SECP',
  project_resource_and_size: 'PRS',
  technical_architecture_type: 'TAT',
  application_architecture_type: 'AAT',
  data_architecture_type: 'DAT',
  business_architecture_type: 'BAT',
  security_architecture_type: 'SAT',
};

const categoryGroupOptions: Array<{ label: string; value: QuestionnaireCategoryGroupKey }> = [
  { label: 'Scale 类(整体)', value: 'scale_overall' },
  { label: '复杂类(整体)', value: 'complexity_overall' },
  { label: '变更类', value: 'change' },
  { label: '架构类型类', value: 'architecture_type' },
];

const categoryGroupLabelMap: Record<QuestionnaireCategoryGroupKey, string> = Object.fromEntries(
  categoryGroupOptions.map((item) => [item.value, item.label]),
) as Record<QuestionnaireCategoryGroupKey, string>;

const optionSections: Array<{ key: OptionSectionKey; label: string }> = [
  { key: 'projectTypeOptions', label: 'Project Types' },
  { key: 'applicationCountRangeOptions', label: 'Applications In Scope' },
  { key: 'externalSystemCountRangeOptions', label: 'External Systems' },
  { key: 'newApplicationCountRangeOptions', label: 'New Applications' },
  { key: 'modifiedApplicationCountRangeOptions', label: 'Modified Applications' },
  { key: 'dataCenterCountRangeOptions', label: 'Data Centers' },
  { key: 'cloudRegionScopeOptions', label: 'Cloud Region Scope' },
  { key: 'techStackKindsCountRangeOptions', label: 'Technology Stack Kinds' },
  { key: 'integrationTechKindsCountRangeOptions', label: 'Integration Technology Kinds' },
];

const optionSectionLabelMap: Record<OptionSectionKey, string> = Object.fromEntries(
  optionSections.map((item) => [item.key, item.label]),
) as Record<OptionSectionKey, string>;

const questionControlOptions: Array<{ label: string; value: QuestionControl }> = [
  { label: 'Single Choice', value: 'radio' },
  { label: 'Dropdown', value: 'select' },
  { label: 'Multi Select', value: 'multiselect' },
  { label: 'Text Input', value: 'text' },
  { label: 'Textarea', value: 'textarea' },
];

function describeQuestionOptions(control: string, optionsSource?: string, options?: Option[]) {
  if (control === 'text' || control === 'textarea') {
    return 'Free text';
  }
  if (optionsSource) {
    return `Source: ${optionSectionLabelMap[optionsSource as OptionSectionKey] || optionsSource}`;
  }
  if ((options || []).length > 0) {
    return `Inline: ${(options || []).length}`;
  }
  return 'No options';
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function nextQuestionId(questions: QuestionConfig[]) {
  return Math.max(0, ...questions.map((item) => Number(item.id) || 0)) + 1;
}

function projectTypeStatusColor(status: ProjectTypeArtifactStatus) {
  switch (status) {
    case 'Mandatory':
      return 'red';
    case 'Recommended':
      return 'blue';
    case 'Optional':
      return 'gold';
    default:
      return 'default';
  }
}

function renderProjectTypeGuide(guide: ProjectTypeGuide, profiles: ProjectTypeProfile[]) {
  return (
    <div className="space-y-4">
      {guide.title && <Typography.Title level={5} style={{ marginBottom: 0 }}>{guide.title}</Typography.Title>}
      {guide.introduction.map((paragraph) => (
        <Typography.Paragraph key={paragraph} style={{ marginBottom: 8 }}>{paragraph}</Typography.Paragraph>
      ))}

      {guide.objectives.length > 0 && (
        <div>
          <Typography.Text strong>Objectives</Typography.Text>
          <div className="mt-2 space-y-2">
            {guide.objectives.map((item) => (
              <div key={item.title} className="rounded border border-slate-200 p-3">
                <Typography.Text strong>{item.title}</Typography.Text>
                <div className="mt-1 text-sm text-slate-600">{item.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(guide.scopeIntro || guide.scopeProjectTypes.length > 0 || guide.scopeNote) && (
        <div>
          <Typography.Text strong>Scope</Typography.Text>
          {guide.scopeIntro && <div className="mt-2 text-sm text-slate-600">{guide.scopeIntro}</div>}
          {guide.scopeProjectTypes.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
              {guide.scopeProjectTypes.map((item) => <li key={item}>{item}</li>)}
            </ul>
          )}
          {guide.scopeNote && <div className="mt-2 text-sm text-slate-600">{guide.scopeNote}</div>}
        </div>
      )}

      {guide.corePrinciples.length > 0 && (
        <div>
          <Typography.Text strong>Core Principles</Typography.Text>
          <div className="mt-2 space-y-2">
            {guide.corePrinciples.map((item) => (
              <div key={item.title} className="rounded border border-slate-200 p-3">
                <Typography.Text strong>{item.title}</Typography.Text>
                <div className="mt-1 text-sm text-slate-600">{item.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {guide.governanceBoundary.length > 0 && (
        <div>
          <Typography.Text strong>EA Governance Boundary</Typography.Text>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
            {guide.governanceBoundary.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}

      {guide.recommendedUsage.length > 0 && (
        <div>
          <Typography.Text strong>Recommended Usage</Typography.Text>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
            {guide.recommendedUsage.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}

      {(guide.artifactSelectionIntro.length > 0 || profiles.length > 0) && (
        <div>
          <Typography.Text strong>Architecture Artifact Selection</Typography.Text>
          {guide.artifactSelectionIntro.map((item) => (
            <div key={item} className="mt-2 text-sm text-slate-600">{item}</div>
          ))}
          {profiles.length > 0 && (
            <div className="mt-3 overflow-x-auto rounded border border-slate-200">
              <table className="min-w-full border-collapse text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Project Type</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Description</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Artifact Baseline</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Typical Patterns</th>
                    <th className="border-b border-slate-200 px-3 py-2 text-left font-semibold">Typical Risks</th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.map((profile) => (
                    <tr key={profile.value}>
                      <td className="border-b border-slate-100 px-3 py-2 align-top font-medium">{profile.label}</td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">{profile.description}</td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top">
                        <div className="flex flex-wrap gap-1">
                          {profile.artifactSelections.map((selection) => (
                            <Tag key={`${profile.value}-${selection.artifactKey}`} color={projectTypeStatusColor(selection.status)}>
                              {selection.artifactLabel}: {selection.status}
                            </Tag>
                          ))}
                        </div>
                      </td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">
                        {profile.typicalPatterns.length > 0 ? profile.typicalPatterns.join(', ') : '-'}
                      </td>
                      <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-600">
                        {profile.typicalRisks.length > 0 ? profile.typicalRisks.join(', ') : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {guide.legend.length > 0 && (
        <div>
          <Typography.Text strong>Legend</Typography.Text>
          <div className="mt-2 flex flex-wrap gap-2">
            {guide.legend.map((item) => (
              <Tag key={item.symbol}>{item.symbol}: {item.meaning}</Tag>
            ))}
          </div>
        </div>
      )}

      {guide.note && (
        <Alert type="info" showIcon title={guide.note} />
      )}
    </div>
  );
}

export default function QuestionnaireConfigPage() {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [categoryForm] = Form.useForm<CategoryFormValues>();
  const [questionForm] = Form.useForm<QuestionFormValues>();
  const [optionForm] = Form.useForm<OptionFormValues>();
  const [optionSetForm] = Form.useForm<OptionSetFormValues>();
  const questionControlValue = Form.useWatch('control', questionForm) as QuestionControl | undefined;
  const questionOptionsSourceValue = Form.useWatch('optionsSource', questionForm) as string | undefined;
  const isAdmin = hasRole('ea_admin');

  const [config, setConfig] = useState<QuestionnaireConfig>(() => mergeQuestionnaireConfig({}));
  const [changeNote, setChangeNote] = useState('');
  const [activeOptionSection, setActiveOptionSection] = useState<string>('questionYesNoOptions');
  const [editingCategory, setEditingCategory] = useState<CategoryConfig | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<QuestionConfig | null>(null);
  const [editingOption, setEditingOption] = useState<Option | null>(null);
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [questionModalOpen, setQuestionModalOpen] = useState(false);
  const [optionModalOpen, setOptionModalOpen] = useState(false);
  const [optionSetModalOpen, setOptionSetModalOpen] = useState(false);
  const [questionnaireSectionsJson, setQuestionnaireSectionsJson] = useState('[]');
  const [questionnaireSectionsError, setQuestionnaireSectionsError] = useState<string | null>(null);
  const [assessmentMatricesJson, setAssessmentMatricesJson] = useState('[]');
  const [assessmentMatricesError, setAssessmentMatricesError] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['avdmQuestionnaireConfig', 'default', 'adminPage'],
    queryFn: () => api.get<QuestionnaireConfigResponse>('/avdm/questionnaire-config', { configKey: 'default' }),
    enabled: isAdmin,
  });

  const serverConfig = useMemo(() => mergeQuestionnaireConfig(data?.config || {}), [data?.config]);

  useEffect(() => {
    if (!data) return;
    setConfig(serverConfig);
    setQuestionnaireSectionsJson(JSON.stringify(serverConfig.questionnaireSections, null, 2));
    setQuestionnaireSectionsError(null);
    setAssessmentMatricesJson(JSON.stringify(serverConfig.assessmentMatrices, null, 2));
    setAssessmentMatricesError(null);
  }, [data, serverConfig]);

  const categoryOptions = useMemo(() => config.questionnaireCategories.map((item) => ({
    label: item.label,
    value: item.key,
  })), [config.questionnaireCategories]);

  const optionSetChoices = useMemo(() => {
    const optionSetKeys = new Set(config.optionSets.map((item) => item.key));
    return [
      ...config.optionSets.map((item) => ({ label: `${item.name} (${item.key})`, value: item.key })),
      ...optionSections
        .filter((item) => !optionSetKeys.has(item.key) && Array.isArray(config[item.key]) && config[item.key].length > 0)
        .map((item) => ({ label: item.label, value: item.key })),
    ];
  }, [config]);

  const activeOptionSet = useMemo(
    () => config.optionSets.find((item) => item.key === activeOptionSection),
    [activeOptionSection, config.optionSets],
  );

  const activeOptionItems = useMemo(() => {
    if (activeOptionSet) {
      return activeOptionSet.options;
    }
    return optionSections.some((item) => item.key === activeOptionSection)
      ? config[activeOptionSection as OptionSectionKey]
      : [];
  }, [activeOptionSection, activeOptionSet, config]);

  const groupedCategorySections = useMemo<CategoryGroupSection[]>(() => {
    const primaryGroups: CategoryGroupSection[] = categoryGroupOptions
      .map((group) => ({
        ...group,
        items: config.questionnaireCategories.filter((category) => category.group === group.value),
      }))
      .filter((group) => group.items.length > 0);

    const ungrouped = config.questionnaireCategories.filter((category) => !category.group);
    if (ungrouped.length > 0) {
      primaryGroups.push({
        label: '未分组',
        value: undefined,
        items: ungrouped,
      });
    }

    return primaryGroups;
  }, [config.questionnaireCategories]);

  const managedQuestionRows = useMemo<ManagedQuestionRow[]>(() => {
    const rows: ManagedQuestionRow[] = [
      ...config.questionBank.map((item) => ({
        rowKey: `questionBank.${item.id}`,
        displayId: '',
        category: item.category,
        text: item.text,
        control: item.control,
        optionsSummary: describeQuestionOptions(item.control, item.optionsSource, item.options),
        designIntent: item.designIntent,
        editable: true,
        sourceTab: item.sourceScope === 'questionnaire_section'
          ? 'questionnaire-sections'
          : item.sourceScope === 'assessment_matrix'
            ? 'assessment-matrices'
            : 'question-bank',
        questionId: item.id,
      })),
    ];

    const categoryGroupByKey = new Map(
      config.questionnaireCategories.map((category) => [category.key, category.group])
    );
    const categoryGroupOrderMap = new Map(
      categoryGroupOptions.map((group, index) => [group.value, index])
    );

    rows.sort((left, right) => {
      const leftGroupOrder = categoryGroupOrderMap.get(categoryGroupByKey.get(left.category) || 'change') ?? Number.MAX_SAFE_INTEGER;
      const rightGroupOrder = categoryGroupOrderMap.get(categoryGroupByKey.get(right.category) || 'change') ?? Number.MAX_SAFE_INTEGER;
      if (leftGroupOrder !== rightGroupOrder) {
        return leftGroupOrder - rightGroupOrder;
      }

      const categoryCompare = left.category.localeCompare(right.category);
      if (categoryCompare !== 0) {
        return categoryCompare;
      }

      const leftQuestionId = left.questionId ?? Number.MAX_SAFE_INTEGER;
      const rightQuestionId = right.questionId ?? Number.MAX_SAFE_INTEGER;
      if (leftQuestionId !== rightQuestionId) {
        return leftQuestionId - rightQuestionId;
      }

      return left.rowKey.localeCompare(right.rowKey);
    });

    const categoryCounters = new Map<string, number>();
    return rows.map((row) => {
      const nextNumber = (categoryCounters.get(row.category) || 0) + 1;
      categoryCounters.set(row.category, nextNumber);
      const prefix = categoryIdPrefixMap[row.category] || row.category.toUpperCase();
      return {
        ...row,
        displayId: `${prefix}${nextNumber}`,
      };
    });
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: async () => api.put<QuestionnaireConfigResponse>(
      '/avdm/questionnaire-config?configKey=default',
      {
        config: mergeQuestionnaireConfig(config),
        changeNote: changeNote || null,
        operator: user?.id || 'system',
      }
    ),
    onSuccess: () => {
      messageApi.success('Questionnaire config saved. New version published.');
      queryClient.invalidateQueries({ queryKey: ['avdmQuestionnaireConfig', 'default'] });
      queryClient.invalidateQueries({ queryKey: ['avdmQuestionnaireConfig', 'default', 'adminPage'] });
      setChangeNote('');
    },
    onError: (error: Error) => {
      messageApi.error(error.message || 'Failed to save questionnaire config');
    },
  });

  const openCategoryEditor = (item?: CategoryConfig) => {
    setEditingCategory(item || null);
    categoryForm.setFieldsValue(item || { key: '' as QuestionnaireCategoryKey, label: '', description: '', group: 'change' as QuestionnaireCategoryGroupKey });
    setCategoryModalOpen(true);
  };

  const openQuestionEditor = (item?: QuestionConfig) => {
    const initial = item || {
      id: nextQuestionId(config.questionBank),
      text: '',
      category: config.questionnaireCategories.find((category) => category.key === 'business_change')?.key
        || config.questionnaireCategories[0]?.key
        || 'business_change',
      designIntent: '',
      control: 'radio' as QuestionControl,
      options: [],
      optionsSource: undefined,
      placeholder: '',
    };
    setEditingQuestion(item || null);
    questionForm.setFieldsValue(initial);
    setQuestionModalOpen(true);
  };

  const openOptionEditor = (item?: Option) => {
    setEditingOption(item || null);
    optionForm.setFieldsValue(item || { label: '', value: '' });
    setOptionModalOpen(true);
  };

  const openOptionSetEditor = () => {
    optionSetForm.setFieldsValue({ key: '', name: '', description: '' });
    setOptionSetModalOpen(true);
  };

  const saveCategory = async () => {
    const values = await categoryForm.validateFields();
    const normalized: CategoryConfig = {
      key: values.key,
      label: values.label.trim(),
      description: values.description?.trim() || '',
      group: values.group,
    };
    setConfig((previous) => {
      const exists = previous.questionnaireCategories.some((item) => item.key === normalized.key);
      return {
        ...previous,
        questionnaireCategories: exists
          ? previous.questionnaireCategories.map((item) => item.key === normalized.key ? normalized : item)
          : [...previous.questionnaireCategories, normalized],
      };
    });
    setCategoryModalOpen(false);
  };

  const saveQuestion = async () => {
    const values = await questionForm.validateFields();
    const control = values.control as QuestionControl;
    const supportsPredefinedOptions = ['radio', 'select', 'multiselect'].includes(control);
    const normalizedOptions: Option[] = Array.isArray(values.options)
      ? values.options
        .filter((item: Option | undefined) => item?.label?.trim() && item?.value?.trim())
        .map((item: Option) => ({ label: item.label.trim(), value: item.value.trim() }))
      : [];

    const normalized: QuestionConfig = {
      id: Number(values.id),
      questionKey: editingQuestion?.questionKey,
      text: values.text.trim(),
      category: values.category,
      designIntent: values.designIntent?.trim() || undefined,
      control,
      options: supportsPredefinedOptions && !values.optionsSource ? normalizedOptions : [],
      optionsSource: supportsPredefinedOptions && values.optionsSource ? values.optionsSource : undefined,
      placeholder: values.placeholder?.trim() || undefined,
      sourceScope: editingQuestion?.sourceScope || 'question_bank',
      sourceRef: editingQuestion?.sourceRef,
    };
    setConfig((previous) => {
      const exists = previous.questionBank.some((item) => item.id === normalized.id);
      return {
        ...previous,
        questionBank: exists
          ? previous.questionBank.map((item) => item.id === normalized.id ? normalized : item)
          : [...previous.questionBank, normalized].sort((a, b) => a.id - b.id),
      };
    });
    setQuestionModalOpen(false);
  };

  const saveOption = async () => {
    const values = await optionForm.validateFields();
    const normalized: Option = {
      label: values.label.trim(),
      value: values.value.trim(),
      score: Number.isFinite(Number(values.score)) ? Number(values.score) : undefined,
    };
    setConfig((previous) => {
      const existingOptionSet = previous.optionSets.find((item) => item.key === activeOptionSection);
      const currentOptions = existingOptionSet?.options || previous[activeOptionSection as OptionSectionKey] || [];
      const exists = currentOptions.some((item) => item.value === normalized.value);
      const nextOptions = exists
        ? currentOptions.map((item) => item.value === normalized.value ? normalized : item)
        : [...currentOptions, normalized];
      if (existingOptionSet) {
        return {
          ...previous,
          optionSets: previous.optionSets.map((item) => item.key === activeOptionSection ? { ...item, options: nextOptions } : item),
        };
      }
      return {
        ...previous,
        [activeOptionSection]: nextOptions,
      };
    });
    setOptionModalOpen(false);
  };

  const saveOptionSet = async () => {
    const values = await optionSetForm.validateFields();
    const normalized: AnswerOptionSetConfig = {
      key: values.key.trim(),
      name: values.name.trim(),
      description: values.description?.trim() || '',
      isShared: true,
      sortOrder: config.optionSets.length * 10 + 10,
      options: [],
    };
    if (config.optionSets.some((item) => item.key === normalized.key)) {
      messageApi.warning('Option set key already exists.');
      return;
    }
    setConfig((previous) => ({
      ...previous,
      optionSets: [...previous.optionSets, normalized],
    }));
    setActiveOptionSection(normalized.key);
    setOptionSetModalOpen(false);
  };

  const deleteCategory = (key: QuestionnaireCategoryKey) => {
    if (config.questionBank.some((item) => item.category === key)) {
      messageApi.warning('This category is used by questions. Move those questions before deleting it.');
      return;
    }
    setConfig((previous) => ({
      ...previous,
      questionnaireCategories: previous.questionnaireCategories.filter((item) => item.key !== key),
    }));
  };

  const deleteQuestion = (id: number) => {
    setConfig((previous) => ({
      ...previous,
      questionBank: previous.questionBank.filter((item) => item.id !== id),
    }));
  };

  const deleteOption = (value: string) => {
    setConfig((previous) => ({
      ...previous,
      optionSets: previous.optionSets.map((item) => item.key === activeOptionSection
        ? { ...item, options: item.options.filter((option) => option.value !== value) }
        : item),
      ...(optionSections.some((item) => item.key === activeOptionSection)
        ? { [activeOptionSection]: previous[activeOptionSection as OptionSectionKey].filter((item) => item.value !== value) }
        : {}),
    }));
  };

  const updateAssessmentMatricesJson = (value: string) => {
    setAssessmentMatricesJson(value);
    try {
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) {
        throw new Error('Assessment matrices JSON must be an array');
      }
      const normalized = mergeQuestionnaireConfig({ assessmentMatrices: parsed }).assessmentMatrices;
      setConfig((previous) => ({
        ...previous,
        assessmentMatrices: normalized,
      }));
      setAssessmentMatricesError(null);
    } catch (error) {
      setAssessmentMatricesError(error instanceof Error ? error.message : 'Invalid JSON');
    }
  };

  const updateQuestionnaireSectionsJson = (value: string) => {
    setQuestionnaireSectionsJson(value);
    try {
      const parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) {
        throw new Error('Questionnaire sections JSON must be an array');
      }
      const normalized = mergeQuestionnaireConfig({ questionnaireSections: parsed }).questionnaireSections;
      setConfig((previous) => ({
        ...previous,
        questionnaireSections: normalized,
      }));
      setQuestionnaireSectionsError(null);
    } catch (error) {
      setQuestionnaireSectionsError(error instanceof Error ? error.message : 'Invalid JSON');
    }
  };

  const renderQuestionnaireSectionSummary = (sections: QuestionnaireSection[]) => (
    <div className="space-y-3">
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        Maintain all backend-driven step-two questionnaire sections as JSON, including configurable checkpoint blocks. Changes are saved into the questionnaire config in the database.
      </Typography.Paragraph>
      {questionnaireSectionsError && <Alert type="error" showIcon title={questionnaireSectionsError} />}
      <Input.TextArea
        rows={24}
        value={questionnaireSectionsJson}
        onChange={(event) => updateQuestionnaireSectionsJson(event.target.value)}
        spellCheck={false}
      />
      <div className="space-y-2">
        {sections.map((section) => (
          <div key={section.key} className="rounded border border-slate-200 p-3">
            <Typography.Text strong>{section.title}</Typography.Text>
            {section.description && <div className="mt-1 text-sm text-slate-600">{section.description}</div>}
            <div className="mt-2 text-xs text-slate-500">{section.fields.length} fields</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAssessmentMatrixSummary = (matrices: AssessmentMatrixSection[]) => (
    <div className="space-y-3">
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        Maintain the backend-driven questionnaire assessment sections as JSON. Changes are saved into the questionnaire config in the database.
      </Typography.Paragraph>
      {assessmentMatricesError && <Alert type="error" showIcon title={assessmentMatricesError} />}
      <Input.TextArea
        rows={24}
        value={assessmentMatricesJson}
        onChange={(event) => updateAssessmentMatricesJson(event.target.value)}
        spellCheck={false}
      />
      <div className="space-y-2">
        {matrices.map((section) => (
          <div key={section.key} className="rounded border border-slate-200 p-3">
            <Typography.Text strong>{section.title}</Typography.Text>
            {section.description && <div className="mt-1 text-sm text-slate-600">{section.description}</div>}
            <div className="mt-2 text-xs text-slate-500">{section.questions.length} questions</div>
          </div>
        ))}
      </div>
    </div>
  );

  const categoryColumns: ColumnsType<CategoryConfig> = [
    { title: 'Key', dataIndex: 'key', width: 160, render: (value) => <Tag color="blue">{value}</Tag> },
    { title: 'Label', dataIndex: 'label', width: 180, render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    { title: 'Description', dataIndex: 'description' },
    {
      title: 'Action',
      key: 'action',
      width: 168,
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openCategoryEditor(record)} />
          <Popconfirm title="Delete category?" onConfirm={() => deleteCategory(record.key)}>
            <Button danger icon={<Trash2 className="h-4 w-4" />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const questionColumns: ColumnsType<ManagedQuestionRow> = [
    { title: 'ID', dataIndex: 'displayId', width: 96 },
    { title: 'Category', dataIndex: 'category', width: 150, render: (value) => <Tag>{value}</Tag> },
    { title: 'Answer Type', dataIndex: 'control', width: 120, render: (value) => <Tag color="blue">{value}</Tag> },
    { title: 'Options', dataIndex: 'optionsSummary', width: 220 },
    { title: 'Question', dataIndex: 'text', render: (value) => <Typography.Text>{value}</Typography.Text> },
    { title: 'Design Intent', dataIndex: 'designIntent', ellipsis: true },
    {
      title: 'Action',
      key: 'action',
      width: 220,
      render: (_, record) => (
        record.editable ? (
          <Space>
            <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openQuestionEditor(config.questionBank.find((item) => item.id === record.questionId))} />
            <Popconfirm title="Delete question?" onConfirm={() => record.questionId && deleteQuestion(record.questionId)}>
              <Button danger icon={<Trash2 className="h-4 w-4" />} />
            </Popconfirm>
          </Space>
        ) : (
          <Typography.Text type="secondary">
            Edit in {record.sourceTab === 'questionnaire-sections' ? 'Questionnaire Sections' : 'Assessment Matrices'}
          </Typography.Text>
        )
      ),
    },
  ];

  const optionColumns: ColumnsType<Option> = [
    { title: 'Label', dataIndex: 'label', render: (value) => <Typography.Text strong>{value}</Typography.Text> },
    { title: 'Value', dataIndex: 'value', width: 220, render: (value) => <Tag>{value}</Tag> },
    { title: 'Score', dataIndex: 'score', width: 120, render: (value) => value ?? '-' },
    {
      title: 'Action',
      key: 'action',
      width: 168,
      render: (_, record) => (
        <Space>
          <Button icon={<Edit3 className="h-4 w-4" />} onClick={() => openOptionEditor(record)} />
          <Popconfirm title="Delete option?" onConfirm={() => deleteOption(record.value)}>
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
        <Alert type="error" showIcon title="Access denied" description="Only EA Admin can maintain questionnaire configuration." />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      {contextHolder}

      <section className="border-b border-slate-200 bg-white pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Typography.Title level={4} style={{ marginBottom: 4 }}>Questionnaire Config Admin</Typography.Title>
            <Typography.Text type="secondary">Maintain step-two categories, questions, sections, and range options through structured controls.</Typography.Text>
          </div>
          <Space wrap>
            <Button icon={<RefreshCw className="h-4 w-4" />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
            <Button icon={<Download className="h-4 w-4" />} onClick={() => downloadJson(`avdm-questionnaire-config-${new Date().toISOString().slice(0, 10)}.json`, mergeQuestionnaireConfig(config))}>Export JSON</Button>
            <Button icon={<RotateCcw className="h-4 w-4" />} onClick={() => setConfig(serverConfig)}>Reset Server Config</Button>
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
          <Input value={changeNote} onChange={(event) => setChangeNote(event.target.value)} placeholder="e.g. 调整问卷问题或分档选项" maxLength={200} />
        </div>

        <Tabs
          items={[
            {
              key: 'questions',
              label: `Questions (${managedQuestionRows.length})`,
              children: (
                <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                  <Alert
                    type="info"
                    showIcon
                    title={`Managed question items: ${managedQuestionRows.length} total (${config.questionBank.filter((item) => (item.sourceScope || 'question_bank') === 'question_bank').length} question bank, ${config.questionBank.filter((item) => item.sourceScope === 'questionnaire_section').length} questionnaire section fields, ${config.questionBank.filter((item) => item.sourceScope === 'assessment_matrix').length} assessment matrix questions).`}
                  />
                  <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openQuestionEditor()}>Add Question</Button>
                  <Table rowKey="rowKey" columns={questionColumns} dataSource={managedQuestionRows} pagination={{ pageSize: 12 }} />
                </Space>
              ),
            },
            {
              key: 'categories',
              label: `Categories (${config.questionnaireCategories.length})`,
              children: (
                <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                  <Alert
                    type="info"
                    showIcon
                    title={`Categories are grouped into 4 classes: ${categoryGroupOptions.map((item) => item.label).join(' / ')}.`}
                  />
                  <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openCategoryEditor()}>Add Category</Button>
                  <div className="space-y-4">
                    {groupedCategorySections.map((group) => (
                      <div key={group.value} className="rounded border border-slate-200 bg-slate-50/40 p-4">
                        <div className="mb-3 flex items-center justify-between gap-3">
                          <div>
                            <Typography.Text strong>{group.label}</Typography.Text>
                            <div className="mt-1 text-xs text-slate-500">{group.items.length} categories</div>
                          </div>
                          {group.value && (
                            <Tag color="purple">{categoryGroupLabelMap[group.value as QuestionnaireCategoryGroupKey]}</Tag>
                          )}
                        </div>
                        <Table
                          rowKey="key"
                          columns={categoryColumns}
                          dataSource={group.items}
                          pagination={false}
                          size="small"
                        />
                      </div>
                    ))}
                  </div>
                </Space>
              ),
            },
            {
              key: 'project-type-guide',
              label: 'Project Type Guide',
              children: renderProjectTypeGuide(config.projectTypeGuide, config.projectTypeProfiles),
            },
            {
              key: 'questionnaire-sections',
              label: 'Questionnaire Sections',
              children: renderQuestionnaireSectionSummary(config.questionnaireSections),
            },
            {
              key: 'assessment-matrices',
              label: 'Assessment Matrices',
              children: renderAssessmentMatrixSummary(config.assessmentMatrices),
            },
            {
              key: 'ranges',
              label: `Option Templates (${optionSetChoices.length})`,
              children: (
                <Space orientation="vertical" size={12} style={{ width: '100%' }}>
                  <Alert
                    type="info"
                    showIcon
                    title="Question answer choices are maintained here and referenced by questions through Options Source. Fill Questionnaire does not create fallback choices."
                  />
                  <Space wrap>
                    <Select value={activeOptionSection} options={optionSetChoices} onChange={setActiveOptionSection} style={{ width: 420 }} />
                    <Button icon={<Plus className="h-4 w-4" />} onClick={() => openOptionSetEditor()}>Add Option Set</Button>
                    <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={() => openOptionEditor()}>Add Option</Button>
                  </Space>
                  {activeOptionSet && (
                    <Typography.Text type="secondary">{activeOptionSet.description || activeOptionSet.key}</Typography.Text>
                  )}
                  <Table rowKey="value" columns={optionColumns} dataSource={activeOptionItems} pagination={false} />
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal title={editingCategory ? 'Edit Category' : 'Add Category'} open={categoryModalOpen} onCancel={() => setCategoryModalOpen(false)} onOk={saveCategory} destroyOnHidden>
        <Form form={categoryForm} layout="vertical">
          <Form.Item name="key" label="Key" rules={[{ required: true }]}>
            <Input disabled={!!editingCategory} placeholder="business_change" />
          </Form.Item>
          <Form.Item name="label" label="Label" rules={[{ required: true }]}>
            <Input placeholder="Business Change" />
          </Form.Item>
          <Form.Item name="group" label="Group" rules={[{ required: true }]}>
            <Select options={categoryGroupOptions} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea autoSize={{ minRows: 3, maxRows: 5 }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={editingQuestion ? 'Edit Question' : 'Add Question'} open={questionModalOpen} onCancel={() => setQuestionModalOpen(false)} onOk={saveQuestion} width={760} destroyOnHidden>
        <Form form={questionForm} layout="vertical">
          <Form.Item name="id" label="Question ID" rules={[{ required: true }]}>
            <Input type="number" disabled={!!editingQuestion} />
          </Form.Item>
          <Form.Item name="category" label="Category" rules={[{ required: true }]}>
            <Select options={categoryOptions} />
          </Form.Item>
          <Form.Item name="control" label="Answer Type" rules={[{ required: true }]}>
            <Select options={questionControlOptions} />
          </Form.Item>
          <Form.Item name="text" label="Question" rules={[{ required: true }]}>
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 5 }} />
          </Form.Item>
          <Form.Item name="placeholder" label="Placeholder">
            <Input placeholder={questionControlValue === 'textarea' ? 'Enter helper text for textarea' : 'Optional placeholder'} />
          </Form.Item>
          {questionControlValue && ['radio', 'select', 'multiselect'].includes(questionControlValue) && (
            <>
              <Form.Item name="optionsSource" label="Options Source">
                <Select
                  allowClear
                  options={optionSetChoices}
                  placeholder="Use an existing Option Template"
                />
              </Form.Item>
              {!questionOptionsSourceValue && (
                <>
                  <Typography.Text strong>Inline Options</Typography.Text>
                  <Form.List name="options">
                    {(fields, { add, remove }) => (
                      <Space orientation="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                        {fields.map((field) => (
                          <Space key={field.key} align="baseline" style={{ width: '100%' }}>
                            <Form.Item
                              {...field}
                              name={[field.name, 'label']}
                              rules={[{ required: true, whitespace: true }]}
                              style={{ flex: 1 }}
                            >
                              <Input placeholder="Option label" />
                            </Form.Item>
                            <Form.Item
                              {...field}
                              name={[field.name, 'value']}
                              rules={[{ required: true, whitespace: true }]}
                              style={{ flex: 1 }}
                            >
                              <Input placeholder="Option value" />
                            </Form.Item>
                            <Button danger icon={<Trash2 className="h-4 w-4" />} onClick={() => remove(field.name)} />
                          </Space>
                        ))}
                        <Button icon={<Plus className="h-4 w-4" />} onClick={() => add({ label: '', value: '' })}>Add Inline Option</Button>
                      </Space>
                    )}
                  </Form.List>
                </>
              )}
            </>
          )}
          <Form.Item name="designIntent" label="Design Intent">
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 5 }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={editingOption ? 'Edit Option' : 'Add Option'} open={optionModalOpen} onCancel={() => setOptionModalOpen(false)} onOk={saveOption} destroyOnHidden>
        <Form form={optionForm} layout="vertical">
          <Form.Item name="label" label="Label" rules={[{ required: true }]}>
            <Input placeholder="5 or fewer" />
          </Form.Item>
          <Form.Item name="value" label="Value" rules={[{ required: true }]}>
            <Input disabled={!!editingOption} placeholder="LE_5" />
          </Form.Item>
          <Form.Item name="score" label="Score">
            <Input type="number" placeholder="Optional numeric score" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="Add Option Set" open={optionSetModalOpen} onCancel={() => setOptionSetModalOpen(false)} onOk={saveOptionSet} destroyOnHidden>
        <Form form={optionSetForm} layout="vertical">
          <Form.Item name="key" label="Key" rules={[{ required: true, whitespace: true }]}>
            <Input placeholder="questionYesNoOptions" />
          </Form.Item>
          <Form.Item name="name" label="Name" rules={[{ required: true, whitespace: true }]}>
            <Input placeholder="Question Yes / No" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
