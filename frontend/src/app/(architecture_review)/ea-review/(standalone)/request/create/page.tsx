'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMediaQuery } from '@/shared/lib/useMediaQuery';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/lib/api';
import { useAuth } from '@/shared/lib/auth-context';
import {
  Steps, Card, Select, Input, Button, Radio, Modal, Space, Alert, message, Typography, Tooltip,
} from 'antd';
import {
  ArrowRightOutlined, UndoOutlined, PlusCircleOutlined, SaveOutlined,
} from '@ant-design/icons';
import { ResourceAutoComplete } from '@/shared/components/ui/ResourceAutoComplete';
import { HomeOutlined } from '@ant-design/icons';
import {
  defaultQuestionnaireFormCopy,
  mergeQuestionnaireConfig,
  mergeConcernMappingConfig,
  type QuestionnaireConfig,
  type ConcernMappingConfig,
  type QuestionConfig,
  type AssessmentMatrixSection,
  type QuestionnaireFieldValue,
  type QuestionnaireSection,
  type ConcernActivationCondition,
  type ConcernActivationRule,
  type ConcernScoreMapping,
} from '@/features/review/stages/preparation';

const { TextArea } = Input;

/* ── Step definitions for left-side vertical stepper ── */
const STEPS = [
  { title: 'Create Request (Project Team)' },
  { title: 'Fill Questionnaire (Project Team)' },
  { title: 'Confirm Concerns (Review Team)' },
];

type QuestionnaireConfigResponse = {
  configKey: string;
  version: number;
  config: Record<string, unknown>;
  source: 'db' | 'default';
};

type ArchitectureAnswer = {
  id: number;
  answer: QuestionnaireFieldValue;
  comment: string;
};

type ConcernActivationContribution = {
  concernKey: string;
  score: number;
  severity: number;
  likelihood: number;
  note: string;
};

type QuestionnaireSectionAnswers = Record<string, Record<string, QuestionnaireFieldValue>>;

const LEGACY_CHECKPOINT_SECTION_KEYS = {
  checkpoint1: 'privacyCheckpoint1Section',
  checkpoint2: 'privacyCheckpoint2Section',
  checkpoint3: 'privacyCheckpoint3Section',
} as const;

const getDefaultQuestionAnswerValue = (question: Pick<QuestionConfig, 'control'>): QuestionnaireFieldValue => (
  question.control === 'multiselect' ? [] : ''
);

const normalizeQuestionAnswerValue = (question: Pick<QuestionConfig, 'control'>, value: unknown): QuestionnaireFieldValue => (
  question.control === 'multiselect' ? normalizeStringArrayValue(value) : normalizeStringValue(value)
);

const getQuestionAnswerStringValue = (value: QuestionnaireFieldValue | undefined) => (
  typeof value === 'string' ? value : ''
);

const getQuestionAnswerArrayValue = (value: QuestionnaireFieldValue | undefined) => (
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
);

const getQuestionAnswerValues = (value: QuestionnaireFieldValue | undefined) => (
  Array.from(new Set(
    Array.isArray(value)
      ? value.filter((item): item is string => typeof item === 'string' && !!item)
      : typeof value === 'string' && value
        ? [value]
        : []
  ))
);

const hasQuestionAnswerValue = (value: QuestionnaireFieldValue | undefined) => (
  Array.isArray(value)
    ? value.some((item) => typeof item === 'string' && item.trim().length > 0)
    : typeof value === 'string' && value.trim().length > 0
);

const defaultArchitectureAnswers = (questions: Array<Pick<QuestionConfig, 'id' | 'control'>>): ArchitectureAnswer[] =>
  questions.map((question) => ({ id: question.id, answer: getDefaultQuestionAnswerValue(question), comment: '' }));

const normalizeStringValue = (value: unknown) => (typeof value === 'string' ? value : '');

const normalizeStringArrayValue = (value: unknown) => (
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : []
);

const getDefaultSectionFieldValue = (field: QuestionnaireSection['fields'][number]): QuestionnaireFieldValue => (
  field.control === 'multiselect' ? [] : ''
);

const getQuestionnaireStringValue = (value: QuestionnaireFieldValue | undefined) => (
  typeof value === 'string' ? value : ''
);

const getQuestionnaireArrayValue = (value: QuestionnaireFieldValue | undefined) => (
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
);

const toLegacyCheckpointSections = (raw: unknown): Record<string, unknown> => {
  const source = raw && typeof raw === 'object' ? { ...(raw as Record<string, unknown>) } : {};
  const checkpoint1 = source.checkpoint1 && typeof source.checkpoint1 === 'object'
    ? source.checkpoint1 as Record<string, unknown>
    : null;
  const checkpoint2 = source.checkpoint2 && typeof source.checkpoint2 === 'object'
    ? source.checkpoint2 as Record<string, unknown>
    : null;
  const checkpoint3 = source.checkpoint3 && typeof source.checkpoint3 === 'object'
    ? source.checkpoint3 as Record<string, unknown>
    : null;

  if (checkpoint1 && !source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint1]) {
    source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint1] = {
      subsidiaries: normalizeStringArrayValue(checkpoint1.subsidiaries),
      hasThirdPartyData: normalizeStringValue(checkpoint1.hasThirdPartyData),
      transferToThirdParty: normalizeStringValue(checkpoint1.transferToThirdParty),
      comments: normalizeStringValue(checkpoint1.comments),
    };
  }

  if (checkpoint2 && !source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint2]) {
    source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint2] = {
      required: normalizeStringValue(checkpoint2.required),
      personalDataType: normalizeStringValue(checkpoint2.personalDataType),
      companyRecords: normalizeStringValue(checkpoint2.companyRecords),
      governmentSecurityData: normalizeStringValue(checkpoint2.governmentSecurityData),
      criticalInfrastructureData: normalizeStringValue(checkpoint2.criticalInfrastructureData),
      comments: normalizeStringValue(checkpoint2.comments),
    };
  }

  if (checkpoint3 && !source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint3]) {
    source[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint3] = {
      required: normalizeStringValue(checkpoint3.required),
      personalDataType: normalizeStringValue(checkpoint3.personalDataType),
      personalDataVolume: normalizeStringValue(checkpoint3.personalDataVolume),
      sensitiveDataVolume: normalizeStringValue(checkpoint3.sensitiveDataVolume),
      ciio: normalizeStringValue(checkpoint3.ciio),
      importantData: normalizeStringValue(checkpoint3.importantData),
      crossBorderTransfer: normalizeStringValue(checkpoint3.crossBorderTransfer),
      comments: normalizeStringValue(checkpoint3.comments),
    };
  }

  return source;
};

/* ── Label helper ── */
function FieldLabel({ label, required }: { label: string; required?: boolean }) {
  return (
    <div className="mb-1 text-sm">
      {required && <span className="text-red-500 mr-0.5">*</span>}
      {label}
    </div>
  );
}

export default function CreateRequestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const isMdUp = useMediaQuery('(min-width: 768px)');
  const [messageApi, contextHolder] = message.useMessage();
  const [step, setStep] = useState(0);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [submitComments, setSubmitComments] = useState('');
  const [isCreateNew, setIsCreateNew] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  // Tracks whether this request was created in the current session (not loaded from URL)
  const [isNewlyCreated, setIsNewlyCreated] = useState(false);
  // Guard against double-clicks during async pre-mutation operations (e.g. project update)
  const [isSaving, setIsSaving] = useState(false);

  /* ── Step 01 form state ── */
  const [form, setForm] = useState({
    projectId: '',
    projectName: '',
    pm: '',
    pmItcode: '',
    dtLead: '',
    dtLeadItcode: '',
    itLead: '',
    itLeadItcode: '',
    reviewScope: 'All' as 'All' | 'Part of Project',
    wsPhase: '',
    requestDesc: '',
  });

  /* ── Step 02 form state (AVDM questionnaire) ── */
  const [projectType, setProjectType] = useState('');
  const [projectComplexity, setProjectComplexity] = useState(0.5);
  const [questionnaireConfigState, setQuestionnaireConfigState] = useState<QuestionnaireConfig>(() => mergeQuestionnaireConfig({}));
  const [concernMappingConfigState, setConcernMappingConfigState] = useState<ConcernMappingConfig>(() => mergeConcernMappingConfig({}));
  const [questionnaireSectionAnswers, setQuestionnaireSectionAnswers] = useState<QuestionnaireSectionAnswers>({});
  const [questionnaireNote, setQuestionnaireNote] = useState('');
  const [assessmentMatrixAnswers, setAssessmentMatrixAnswers] = useState<Record<string, Record<string, string>>>({});
  const [architectureAnswers, setArchitectureAnswers] = useState<ArchitectureAnswer[]>(
    []
  );

  const activeQuestionBank = useMemo(() => questionnaireConfigState.questionBank.filter((question) => (question.sourceScope || 'question_bank') === 'question_bank'), [questionnaireConfigState.questionBank]);
  const activeQuestionnaireCategories = questionnaireConfigState.questionnaireCategories;
  const formCopy = defaultQuestionnaireFormCopy;
  const selectedProjectTypeProfile = questionnaireConfigState.projectTypeProfiles.find((item) => item.value === projectType);
  const projectTypeGuide = questionnaireConfigState.projectTypeGuide;
  const questionnaireSections = questionnaireConfigState.questionnaireSections;

  const buildDefaultQuestionnaireSectionAnswers = (sections: QuestionnaireSection[]) => Object.fromEntries(
    sections.map((section) => [
      section.key,
      Object.fromEntries(section.fields.map((field) => [field.key, getDefaultSectionFieldValue(field)])),
    ])
  ) as QuestionnaireSectionAnswers;

  const mergeQuestionnaireSectionAnswers = (
    sections: QuestionnaireSection[],
    raw: unknown,
  ): QuestionnaireSectionAnswers => {
    const defaults = buildDefaultQuestionnaireSectionAnswers(sections);
    const source = toLegacyCheckpointSections(raw) as Record<string, Record<string, unknown>>;
    return Object.fromEntries(
      sections.map((section) => {
        const current = source[section.key] && typeof source[section.key] === 'object' ? source[section.key] : {};
        return [
          section.key,
          Object.fromEntries(
            section.fields.map((field) => [
              field.key,
              field.control === 'multiselect'
                ? getQuestionnaireArrayValue(current[field.key] as QuestionnaireFieldValue | undefined)
                : typeof current[field.key] === 'string'
                  ? String(current[field.key])
                  : defaults[section.key]?.[field.key] ?? getDefaultSectionFieldValue(field),
            ])
          ),
        ];
      })
    ) as QuestionnaireSectionAnswers;
  };

  const matchesQuestionnaireFieldCondition = (
    condition: { field: string; equals?: string; in?: string[]; notEquals?: string },
    sectionValues: Record<string, QuestionnaireFieldValue>,
  ) => {
    const rawValue = sectionValues[condition.field];
    const values = Array.isArray(rawValue) ? rawValue : [rawValue ?? ''];
    if (condition.equals !== undefined && !values.includes(condition.equals)) return false;
    if (condition.notEquals !== undefined && values.includes(condition.notEquals)) return false;
    if (condition.in?.length && !values.some((value) => typeof value === 'string' && condition.in?.includes(value))) return false;
    return true;
  };

  const isQuestionnaireFieldEnabled = (
    field: QuestionnaireSection['fields'][number],
    sectionValues: Record<string, QuestionnaireFieldValue>,
  ) => !field.enabledWhen?.length || field.enabledWhen.every((condition) => matchesQuestionnaireFieldCondition(condition, sectionValues));

  const isQuestionnaireFieldRequired = (
    field: QuestionnaireSection['fields'][number],
    sectionValues: Record<string, QuestionnaireFieldValue>,
  ) => (
    field.required
    || (!!field.requiredWhen?.length && field.requiredWhen.every((condition) => matchesQuestionnaireFieldCondition(condition, sectionValues)))
  );

  const rangeOptionSourceMap: Record<string, { label: string; value: string }[]> = {
    ...Object.fromEntries(
      questionnaireConfigState.optionSets.map((optionSet) => [optionSet.key, optionSet.options]),
    ),
    applicationCountRangeOptions: questionnaireConfigState.applicationCountRangeOptions,
    externalSystemCountRangeOptions: questionnaireConfigState.externalSystemCountRangeOptions,
    newApplicationCountRangeOptions: questionnaireConfigState.newApplicationCountRangeOptions,
    modifiedApplicationCountRangeOptions: questionnaireConfigState.modifiedApplicationCountRangeOptions,
    dataCenterCountRangeOptions: questionnaireConfigState.dataCenterCountRangeOptions,
    cloudRegionScopeOptions: questionnaireConfigState.cloudRegionScopeOptions,
    techStackKindsCountRangeOptions: questionnaireConfigState.techStackKindsCountRangeOptions,
    integrationTechKindsCountRangeOptions: questionnaireConfigState.integrationTechKindsCountRangeOptions,
  };

  const resolveQuestionOptions = (question: Pick<QuestionConfig, 'options' | 'optionsSource'>) => (
    question.optionsSource
      ? (rangeOptionSourceMap[question.optionsSource] || question.options || [])
      : question.options || []
  );

  const updateQuestionnaireSectionField = (sectionKey: string, fieldKey: string, value: QuestionnaireFieldValue) => {
    setQuestionnaireSectionAnswers((previous) => {
      const sectionConfig = questionnaireSections.find((item) => item.key === sectionKey);
      const nextSection = {
        ...(previous[sectionKey] || {}),
        [fieldKey]: value,
      };

      sectionConfig?.fields.forEach((field) => {
        if (!isQuestionnaireFieldEnabled(field, nextSection) && field.clearWhenDisabled !== false) {
          nextSection[field.key] = getDefaultSectionFieldValue(field);
        }
      });

      return {
        ...previous,
        [sectionKey]: nextSection,
      };
    });
  };

  const projectScaleSectionValues = questionnaireSectionAnswers.projectScaleSection || {};
  const changeScopeSectionValues = questionnaireSectionAnswers.changeScopeSection || {};
  const complexitySectionValues = questionnaireSectionAnswers.complexitySection || {};
  const checkpoint1Section = questionnaireSectionAnswers[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint1] || {};
  const checkpoint2Section = questionnaireSectionAnswers[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint2] || {};
  const checkpoint3Section = questionnaireSectionAnswers[LEGACY_CHECKPOINT_SECTION_KEYS.checkpoint3] || {};

  const projectScaleSection = {
    applicationsInScope: getQuestionnaireStringValue(projectScaleSectionValues.applicationsInScope),
    hasExternalSystems: getQuestionnaireStringValue(projectScaleSectionValues.hasExternalSystems) as '' | 'Yes' | 'No',
    externalSystemsCount: getQuestionnaireStringValue(projectScaleSectionValues.externalSystemsCount),
  };

  const changeScopeSection = {
    hasNewApplications: getQuestionnaireStringValue(changeScopeSectionValues.hasNewApplications) as '' | 'Yes' | 'No',
    newApplicationsCount: getQuestionnaireStringValue(changeScopeSectionValues.newApplicationsCount),
    modifiedApplicationsCount: getQuestionnaireStringValue(changeScopeSectionValues.modifiedApplicationsCount),
  };

  const complexitySection = {
    dataCenterCount: getQuestionnaireStringValue(complexitySectionValues.dataCenterCount),
    cloudRegionScope: getQuestionnaireStringValue(complexitySectionValues.cloudRegionScope),
    hasCrossBorderDataFlow: getQuestionnaireStringValue(complexitySectionValues.hasCrossBorderDataFlow) as '' | 'Yes' | 'No',
    techStackKindsCount: getQuestionnaireStringValue(complexitySectionValues.techStackKindsCount),
    integrationTechKindsCount: getQuestionnaireStringValue(complexitySectionValues.integrationTechKindsCount),
  };

  const checkpoint1 = {
    subsidiaries: getQuestionnaireArrayValue(checkpoint1Section.subsidiaries),
    hasThirdPartyData: getQuestionnaireStringValue(checkpoint1Section.hasThirdPartyData) as '' | 'Yes' | 'No',
    transferToThirdParty: getQuestionnaireStringValue(checkpoint1Section.transferToThirdParty) as '' | 'Yes' | 'No',
    comments: getQuestionnaireStringValue(checkpoint1Section.comments),
  };

  const checkpoint2 = {
    required: getQuestionnaireStringValue(checkpoint2Section.required) as '' | 'Yes' | 'No',
    personalDataType: getQuestionnaireStringValue(checkpoint2Section.personalDataType),
    companyRecords: getQuestionnaireStringValue(checkpoint2Section.companyRecords),
    governmentSecurityData: getQuestionnaireStringValue(checkpoint2Section.governmentSecurityData) as '' | 'Yes' | 'No',
    criticalInfrastructureData: getQuestionnaireStringValue(checkpoint2Section.criticalInfrastructureData) as '' | 'Yes' | 'No',
    comments: getQuestionnaireStringValue(checkpoint2Section.comments),
  };

  const checkpoint3 = {
    required: getQuestionnaireStringValue(checkpoint3Section.required) as '' | 'Yes' | 'No',
    personalDataType: getQuestionnaireStringValue(checkpoint3Section.personalDataType),
    personalDataVolume: getQuestionnaireStringValue(checkpoint3Section.personalDataVolume),
    sensitiveDataVolume: getQuestionnaireStringValue(checkpoint3Section.sensitiveDataVolume),
    ciio: getQuestionnaireStringValue(checkpoint3Section.ciio) as '' | 'Yes' | 'No' | 'Not Sure',
    importantData: getQuestionnaireStringValue(checkpoint3Section.importantData) as '' | 'Yes' | 'No' | 'Not Sure',
    crossBorderTransfer: getQuestionnaireStringValue(checkpoint3Section.crossBorderTransfer) as '' | 'Yes' | 'No' | 'Not Sure',
    comments: getQuestionnaireStringValue(checkpoint3Section.comments),
  };

  const buildDefaultAssessmentMatrixAnswers = (sections: AssessmentMatrixSection[]) => Object.fromEntries(
    sections.map((section) => [
      section.key,
      Object.fromEntries(section.questions.map((question) => [question.key, ''])),
    ])
  );

  const mergeAssessmentMatrixAnswers = (
    sections: AssessmentMatrixSection[],
    raw: unknown,
  ): Record<string, Record<string, string>> => {
    const defaults = buildDefaultAssessmentMatrixAnswers(sections);
    const source = raw && typeof raw === 'object' ? raw as Record<string, Record<string, unknown>> : {};

    return Object.fromEntries(
      sections.map((section) => {
        const current = source[section.key] && typeof source[section.key] === 'object'
          ? source[section.key]
          : {};
        return [
          section.key,
          Object.fromEntries(
            section.questions.map((question) => [
              question.key,
              typeof current[question.key] === 'string' ? String(current[question.key]) : defaults[section.key]?.[question.key] || '',
            ])
          ),
        ];
      })
    );
  };

  const calculateAssessmentMatrixSectionScore = (section: AssessmentMatrixSection) => {
    const sectionAnswers = assessmentMatrixAnswers[section.key] || {};
    let earned = 0;
    let maximum = 0;
    section.questions.forEach((question) => {
      const weight = Number(question.weight || 1);
      const selected = question.options.find((option) => option.value === sectionAnswers[question.key]);
      const maxScore = Math.max(0, ...question.options.map((option) => Number(option.score || 0)));
      maximum += maxScore * weight;
      earned += Number(selected?.score || 0) * weight;
    });
    return { earned, maximum };
  };

  const derivedProjectComplexity = (() => {
    const relevantSections = questionnaireConfigState.assessmentMatrices.filter((section) =>
      ['requirementComplexitySection', 'solutionComplexitySection', 'resourceSizeSection'].includes(section.key)
    );
    if (relevantSections.length === 0) {
      return null;
    }
    const allAnswered = relevantSections.every((section) =>
      section.questions.every((question) => !!(assessmentMatrixAnswers[section.key] || {})[question.key])
    );
    if (!allAnswered) {
      return null;
    }

    const totals = relevantSections.reduce(
      (summary, section) => {
        const score = calculateAssessmentMatrixSectionScore(section);
        return {
          earned: summary.earned + score.earned,
          maximum: summary.maximum + score.maximum,
        };
      },
      { earned: 0, maximum: 0 },
    );
    if (totals.maximum <= 0) {
      return null;
    }
    return Number((totals.earned / totals.maximum).toFixed(4));
  })();

  const projectTypeStatusClass = (status: string) => {
    if (status === 'Mandatory') return 'bg-red-50 text-red-700 border-red-200';
    if (status === 'Recommended') return 'bg-blue-50 text-blue-700 border-blue-200';
    if (status === 'Optional') return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const getQuestionById = (id: number): QuestionConfig | undefined => (
    questionnaireConfigState.questionBank.find((q) => q.id === id)
  );

  const answerByQuestionId = () => new Map(architectureAnswers.map((item) => [item.id, item]));

  const valueFromSource = (source: string) => {
    const questionMatch = source.match(/^question\.(\d+)\.(answer|comment)$/);
    if (questionMatch) {
      const questionId = Number(questionMatch[1]);
      const field = questionMatch[2] as 'answer' | 'comment';
      return answerByQuestionId().get(questionId)?.[field] ?? '';
    }

    const sourceRoots: Record<string, any> = {
      ...questionnaireSectionAnswers,
      ...assessmentMatrixAnswers,
      checkpoint1,
      checkpoint2,
      checkpoint3,
    };
    const [root, field] = source.split('.');
    return sourceRoots[root]?.[field] ?? '';
  };

  const conditionMatches = (condition: ConcernActivationCondition) => {
    const value = valueFromSource(condition.source);
    const values = Array.isArray(value)
      ? value.filter((item): item is string | number | boolean => ['string', 'number', 'boolean'].includes(typeof item))
      : [value].filter((item): item is string | number | boolean => ['string', 'number', 'boolean'].includes(typeof item));
    if (condition.equals !== undefined && !values.includes(condition.equals)) return false;
    if (condition.notEquals !== undefined && values.includes(condition.notEquals)) return false;
    if (condition.in && !values.some((item) => condition.in?.includes(item))) return false;
    return true;
  };

  const ruleMatches = (rule: ConcernActivationRule) => {
    const allMatches = !rule.all?.length || rule.all.every(conditionMatches);
    const anyMatches = !rule.any?.length || rule.any.some(conditionMatches);
    return allMatches && anyMatches;
  };

  const clampRiskLevel = (value: number) => Math.min(5, Math.max(1, Math.ceil(value)));

  const riskLevelsFromScore = (score: number) => {
    const cappedScore = Math.min(25, Math.max(1, score));
    const severity = clampRiskLevel(Math.sqrt(cappedScore));
    const likelihood = clampRiskLevel(cappedScore / severity);
    return { severity, likelihood };
  };

  const scoreFromRiskLevels = (severity: number, likelihood: number) => severity * likelihood;

  const toContributions = (
    concernScores: ConcernScoreMapping[],
    note: string,
  ): ConcernActivationContribution[] => (
    concernScores
      .filter((item) => item.concernKey)
      .map((item) => {
        const score = Number.isFinite(item.score)
          ? item.score
          : scoreFromRiskLevels(item.severity || 4, item.likelihood || 4);
        const { severity, likelihood } = riskLevelsFromScore(score);
        return {
          concernKey: item.concernKey,
          score,
          severity: item.severity || severity,
          likelihood: item.likelihood || likelihood,
          note: item.note || note,
        };
      })
  );

  const buildConcernActivationContributions = () => {
    const contributions: ConcernActivationContribution[] = [];
    architectureAnswers.forEach((item) => {
      getQuestionAnswerValues(item.answer).forEach((selectedAnswer) => {
        const question = getQuestionById(item.id);
        concernMappingConfigState.questionConcernMappings
          .filter((mapping) => mapping.questionId === item.id && mapping.answer === selectedAnswer)
          .forEach((mapping) => {
            contributions.push(...toContributions(
              mapping.concernScores,
              item.comment || question?.text || `Question ${item.id} selected ${selectedAnswer}`,
            ));
          });
      });
    });

    questionnaireConfigState.assessmentMatrices.forEach((section) => {
      const sectionAnswers = assessmentMatrixAnswers[section.key] || {};
      section.questions.forEach((question) => {
        if (!question.id) {
          return;
        }
        const selectedAnswer = sectionAnswers[question.key];
        if (!selectedAnswer) {
          return;
        }
        concernMappingConfigState.questionConcernMappings
          .filter((mapping) => mapping.questionId === question.id && mapping.answer === selectedAnswer)
          .forEach((mapping) => {
            contributions.push(...toContributions(
              mapping.concernScores,
              question.helperText || question.title || `Assessment matrix question ${question.id} selected ${selectedAnswer}`,
            ));
          });
      });
    });

    concernMappingConfigState.concernActivationRules
      .filter(ruleMatches)
      .forEach((rule) => {
        contributions.push(...toContributions(
          rule.concernScores,
          rule.description,
        ));
      });

    return contributions;
  };

  const buildAggregatedConcernActivations = () => {
    const activationMap = new Map<string, ConcernActivationContribution>();
    buildConcernActivationContributions().forEach((item) => {
      const existing = activationMap.get(item.concernKey);
      if (!existing) {
        activationMap.set(item.concernKey, item);
        return;
      }
      activationMap.set(item.concernKey, {
        concernKey: item.concernKey,
        score: existing.score + item.score,
        ...riskLevelsFromScore(existing.score + item.score),
        note: [existing.note, item.note].filter(Boolean).join('; '),
      });
    });
    return Array.from(activationMap.values());
  };

  const buildActivatedConcernKeys = () => buildAggregatedConcernActivations().map((item) => item.concernKey);

  const buildQuestionnaireRiskAnswers = () => buildAggregatedConcernActivations().map((item) => ({
    riskCode: item.concernKey,
    severity: item.severity,
    likelihood: item.likelihood,
    note: `${item.note || 'Activated by AVDM questionnaire mapping/rules'} (aggregated mapping score: ${item.score})`,
  }));

  const set = (key: string, val: string) => setForm((p) => ({ ...p, [key]: val }));

  /* ── Restore from URL ?id= ── */
  const urlId = searchParams?.get('id') ?? null;
  const queryClient = useQueryClient();

  const { data: existingRequest, refetch: refetchRequest } = useQuery({
    queryKey: ['ea-request-detail', urlId || requestId],
    queryFn: () => api.get<any>(`/ea-requests/${urlId || requestId}`),
    enabled: !!(urlId || requestId),
  });

  const { data: questionnaireConfigResp } = useQuery({
    queryKey: ['avdmQuestionnaireConfig', 'default'],
    queryFn: () => api.get<QuestionnaireConfigResponse>('/avdm/questionnaire-config', { configKey: 'default' }),
  });

  const { data: concernMappingConfigResp } = useQuery({
    queryKey: ['avdmConcernMappingConfig', 'default'],
    queryFn: () => api.get<QuestionnaireConfigResponse>('/avdm/concern-mapping-config', { configKey: 'default' }),
  });

  useEffect(() => {
    if (questionnaireConfigResp?.config) {
      setQuestionnaireConfigState(mergeQuestionnaireConfig(questionnaireConfigResp.config));
    }
  }, [questionnaireConfigResp]);

  useEffect(() => {
    setQuestionnaireSectionAnswers((previous) => mergeQuestionnaireSectionAnswers(questionnaireSections, previous));
  }, [questionnaireSections]);

  useEffect(() => {
    setAssessmentMatrixAnswers((previous) => mergeAssessmentMatrixAnswers(questionnaireConfigState.assessmentMatrices, previous));
  }, [questionnaireConfigState.assessmentMatrices]);

  useEffect(() => {
    if (concernMappingConfigResp?.config) {
      setConcernMappingConfigState(mergeConcernMappingConfig(concernMappingConfigResp.config));
    }
  }, [concernMappingConfigResp]);

  useEffect(() => {
    setArchitectureAnswers((prev) => {
      const prevMap = new Map(prev.map((item) => [item.id, item]));
      return activeQuestionBank.map((question) => {
        const previous = prevMap.get(question.id);
        return {
          id: question.id,
          answer: normalizeQuestionAnswerValue(question, previous?.answer),
          comment: previous?.comment || '',
        };
      });
    });
  }, [activeQuestionBank]);

  useEffect(() => {
    if (existingRequest) {
      const r = existingRequest;
      // Set requestId only if not already set
      if (!requestId) {
        setRequestId(r.requestId || r.id);
      }
      
      // Always update form data and attachments when existingRequest changes
      setForm({
        projectId: r.projectId || '',
        projectName: r.requestName || r.projectName || '',
        pm: r.pm || '',
        pmItcode: r.pmItcode || '',
        dtLead: r.dtLead || '',
        dtLeadItcode: r.dtLeadItcode || '',
        itLead: r.itLead || '',
        itLeadItcode: r.itLeadItcode || '',
        reviewScope: r.reviewScope || 'All',
        wsPhase: r.wsPhase || '',
        requestDesc: r.requestDesc || '',
      });
      
      // Determine which step to show on initial load
      if (!requestId && r.requestId) {
        const nonDraftStatuses = ['Submitted', 'In Progress', 'Completed', 'Accepted by EA', 'Approved', 'Rejected', 'Approved with Actions'];
        if (nonDraftStatuses.includes(r.status)) {
          setStep(1);
        } else {
          setStep(0);
        }
      }
    }
  }, [existingRequest]);

  useEffect(() => {
    if (!form.projectId) return;
    let active = true;
    (async () => {
      try {
        const assessment = await api.get<any>(`/avdm/projects/${encodeURIComponent(form.projectId)}`);
        if (!active || !assessment) return;
        setProjectType(assessment.projectType || '');
        setProjectComplexity(Number(assessment.projectComplexity ?? 0.5));
        setQuestionnaireSectionAnswers(
          toLegacyCheckpointSections(assessment.questionnaire) as QuestionnaireSectionAnswers
        );
        setQuestionnaireNote(String(assessment.questionnaire?.note || ''));
        setAssessmentMatrixAnswers(
          assessment.questionnaire?.assessmentMatrices && typeof assessment.questionnaire.assessmentMatrices === 'object'
            ? assessment.questionnaire.assessmentMatrices
            : {}
        );
        if (Array.isArray(assessment.questionnaire?.architectureAnswers)) {
          const savedMap = new Map<number, { answer: QuestionnaireFieldValue; comment: string }>();
          assessment.questionnaire.architectureAnswers.forEach((item: any) => {
            const id = Number(item.id);
            savedMap.set(id, {
              answer: item.answer,
              comment: String(item.comment || ''),
            });
          });
          setArchitectureAnswers(
            activeQuestionBank.map((question) => ({
              id: question.id,
              answer: normalizeQuestionAnswerValue(question, savedMap.get(question.id)?.answer),
              comment: savedMap.get(question.id)?.comment || '',
            }))
          );
        }
      } catch {
        // ignore when assessment is not created yet
      }
    })();
    return () => {
      active = false;
    };
  }, [form.projectId]);

  /* ── Project search (remote, debounced) ── */
  const [projectSearchText, setProjectSearchText] = useState('');
  const [debouncedProjectSearch, setDebouncedProjectSearch] = useState('');
  const projectSearchTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const handleProjectSearch = useCallback((text: string) => {
    setProjectSearchText(text);
    clearTimeout(projectSearchTimer.current);
    projectSearchTimer.current = setTimeout(() => {
      setDebouncedProjectSearch(text);
    }, 350);
  }, []);

  // Clean up debounce timer on unmount
  useEffect(() => () => clearTimeout(projectSearchTimer.current), []);

  const { data: projectsData, isFetching: isProjectsLoading } = useQuery({
    queryKey: ['projectSearch', debouncedProjectSearch],
    queryFn: () => api.get<any>('/projects', { q: debouncedProjectSearch || undefined, page: 1, pageSize: 30 }),
  });
  const projects: any[] = projectsData?.data ?? [];

  // Keep track of the currently selected project separately (so it survives search changes)
  const [selectedProject, setSelectedProject] = useState<any>(null);

  // When an existing request loads, fetch its project details once
  const { data: existingProjectDetail } = useQuery({
    queryKey: ['projectDetail', form.projectId],
    queryFn: () => api.get<any>(`/projects/${form.projectId}`),
    enabled: !!form.projectId && !selectedProject,
    staleTime: 5 * 60_000,
  });

  /* ── Determine if the current form project came from MSPO (has a source) ── */
  const currentProjectFromList = selectedProject || existingProjectDetail || null;

  /* ── When project selected, auto-fill fields ── */
  const handleProjectChange = (val: string) => {
    const proj = projects.find((p: any) => p.projectId === val);
    if (proj) setSelectedProject(proj);
    setForm((prev) => ({
      ...prev,
      projectId: val || '',
      projectName: proj?.projectName || '',
      pm: proj?.pm || '',
      pmItcode: proj?.pmItcode || '',
      dtLead: proj?.dtLead || '',
      dtLeadItcode: proj?.dtLeadItcode || '',
      itLead: proj?.itLead || '',
      itLeadItcode: proj?.itLeadItcode || '',
    }));
  };

  /* ── Create / Update mutations ── */
  const buildPayload = (extra?: Record<string, any>) => ({
    projectId: form.projectId || null,
    reviewScope: form.reviewScope || null,
    wsPhase: form.reviewScope === 'Part of Project' ? form.wsPhase || null : null,
    requester: user?.id || null,
    organization: 'DTIT',
    link: null,
    requestDesc: form.requestDesc || null,
    assignReviewer: [],
    ...extra,
  });

  /* Save Draft (Step 01 �?Step 02 transition, or explicit "Save as Draft") */
  const saveDraftMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (requestId) {
        // Update existing
        return api.put<any>(`/ea-requests/${requestId}`, payload);
      } else {
        // Create new
        return api.post<any>('/ea-requests', payload);
      }
    },
    onSuccess: (data: any) => {
      const rid = data?.requestId || data?.id || requestId;
      if (rid && !requestId) {
        setRequestId(rid);
        setIsNewlyCreated(true);
        // Update URL with ?id= without full navigation
        const url = new URL(window.location.href);
        url.searchParams.set('id', rid);
        window.history.replaceState({}, '', url.toString());
      }
      // Invalidate cached request detail so navigating back shows fresh data
      queryClient.invalidateQueries({ queryKey: ['ea-request-detail'] });
      queryClient.invalidateQueries({ queryKey: ['eaRequest'] });
      queryClient.invalidateQueries({ queryKey: ['eaRequests'] });
      messageApi.success('Draft saved');
    },
    onError: () => {
      messageApi.error('Failed to save draft');
    },
  });

  const handleSaveAndNext = async () => {
    if (isSaving || saveDraftMutation.isPending) return;
    const isInitialCreate = !requestId && !urlId;
    if (!isCreateNew && !form.projectId) {
      messageApi.error('Please select a project first');
      return;
    }
    if (isCreateNew && !form.projectName) {
      messageApi.error('Please enter a project name');
      return;
    }
    if (!form.pm) {
      messageApi.error('Please enter PM');
      return;
    }
    if (!isProjectFromMspo && !form.dtLead) {
      messageApi.error('Please enter Biz Analyst');
      return;
    }
    if (!isProjectFromMspo && !form.itLead) {
      messageApi.error('Please enter IT Lead');
      return;
    }

    setIsSaving(true);
    try {
      // If creating new project, create project first
      if (isCreateNew) {
        try {
          const projectPayload = {
            projectName: form.projectName,
            pm: form.pm,
            pmItcode: form.pmItcode,
            dtLead: form.dtLead,
            dtLeadItcode: form.dtLeadItcode,
            itLead: form.itLead,
            itLeadItcode: form.itLeadItcode,
          };
          const createdProject = await api.post<any>('/projects', projectPayload);
          const newProjectId = createdProject.projectId;

          // Update form with new project ID
          setForm((prev) => ({ ...prev, projectId: newProjectId }));

          // Save EA request with new project ID
          saveDraftMutation.mutate(buildPayload({
            projectId: newProjectId,
            ...(isInitialCreate ? { link: null } : {}),
          }), {
            onSuccess: () => {
              if (!requestId && !urlId) {
                setProjectType('');
                setProjectComplexity(0.5);
                setQuestionnaireSectionAnswers(buildDefaultQuestionnaireSectionAnswers(questionnaireSections));
                setQuestionnaireNote('');
                setArchitectureAnswers(defaultArchitectureAnswers(activeQuestionBank));
              }
              setStep(1);
            },
          });
        } catch (error) {
          messageApi.error('Failed to create project');
        }
      } else {
        saveDraftMutation.mutate(buildPayload(isInitialCreate ? { link: null } : undefined), {
          onSuccess: () => {
            if (!requestId && !urlId) {
              setProjectType('');
              setProjectComplexity(0.5);
              setQuestionnaireSectionAnswers(buildDefaultQuestionnaireSectionAnswers(questionnaireSections));
              setQuestionnaireNote('');
              setArchitectureAnswers(defaultArchitectureAnswers(activeQuestionBank));
            }
            setStep(1);
          },
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveDraft = async () => {
    if (isSaving || saveDraftMutation.isPending) return;
    if (!isCreateNew && !form.projectId) {
      messageApi.error('Please select a project first');
      return;
    }
    if (isCreateNew && !form.projectName) {
      messageApi.error('Please enter a project name');
      return;
    }
    if (!form.pm) {
      messageApi.error('Please enter PM');
      return;
    }
    if (!isProjectFromMspo && !form.dtLead) {
      messageApi.error('Please enter Biz Analyst');
      return;
    }
    if (!isProjectFromMspo && !form.itLead) {
      messageApi.error('Please enter IT Lead');
      return;
    }

    setIsSaving(true);
    try {
      // If creating new project, create project first
      if (isCreateNew) {
        try {
          const projectPayload = {
            projectName: form.projectName,
            pm: form.pm,
            pmItcode: form.pmItcode,
            dtLead: form.dtLead,
            dtLeadItcode: form.dtLeadItcode,
            itLead: form.itLead,
            itLeadItcode: form.itLeadItcode,
          };
          const createdProject = await api.post<any>('/projects', projectPayload);
          const newProjectId = createdProject.projectId;

          // Update form with new project ID
          setForm((prev) => ({ ...prev, projectId: newProjectId }));

          // Save EA request with new project ID
          saveDraftMutation.mutate(buildPayload({ projectId: newProjectId }));
        } catch (error) {
          messageApi.error('Failed to create project');
        }
      } else {
        saveDraftMutation.mutate(buildPayload());
      }
    } finally {
      setIsSaving(false);
    }
  };

  /* Submit (Step 02 �?Step 03) */
  const submitMutation = useMutation({
    mutationFn: (payload: any) => {
      if (requestId) {
        return api.put<any>(`/ea-requests/${requestId}`, payload);
      }
      return api.post<any>('/ea-requests', payload);
    },
    onSuccess: (data: any) => {
      messageApi.success('Request submitted successfully');
      const rid = data?.requestId || data?.id || requestId;
      if (rid && !requestId) {
        setRequestId(rid);
        const url = new URL(window.location.href);
        url.searchParams.set('id', rid);
        window.history.replaceState({}, '', url.toString());
      }
      // Refresh request detail (status changes to Submitted)
      queryClient.invalidateQueries({ queryKey: ['ea-request-detail', urlId || rid] });
      if (rid) {
        router.replace(`/request/${rid}`);
      }
    },
    onError: () => {
      messageApi.error('Failed to submit request');
    },
  });

  const handleConfirmSubmit = () => {
    if (!isCreateNew && !form.projectId) {
      messageApi.error('Please select a project first');
      return;
    }
    if (isCreateNew && !form.projectName) {
      messageApi.error('Please enter a project name');
      return;
    }
    questionnaireMutation.mutate({
      projectType: projectType || null,
      projectComplexity: derivedProjectComplexity ?? projectComplexity,
      questionnaire: {
        ...questionnaireSectionAnswers,
        assessmentMatrices: assessmentMatrixAnswers,
        note: questionnaireNote,
        architectureAnswers,
        activatedConcernKeys: buildActivatedConcernKeys(),
        checkpoint1,
        checkpoint2,
        checkpoint3,
      },
      answers: buildQuestionnaireRiskAnswers(),
      status: 'submitted',
      operator: user?.id || 'system',
    }, {
      onSuccess: () => {
        submitMutation.mutate(buildPayload({
          status: 'Submitted',
          updatedBy: user?.id || null,
          statusRemark: submitComments || null,
        }));
      },
    });
    setShowConfirmModal(false);
  };

  const questionnaireMutation = useMutation({
    mutationFn: (payload: any) => {
      if (!form.projectId) throw new Error('Project ID is required');
      return api.post<any>(`/avdm/projects/${encodeURIComponent(form.projectId)}/questionnaire`, payload);
    },
    onError: () => {
      messageApi.error('Failed to save questionnaire');
    },
  });

  /* ── Validation ── */
  const canGoToStep2 = isCreateNew ? !!form.projectName : !!form.projectId;

  // Step 02 submit validation: questionnaire must contain at least one risk item.
  const questionnaireSectionsValid = questionnaireSections.every((section) => {
    const sectionValues = questionnaireSectionAnswers[section.key] || {};
    return section.fields.every((field) => {
      if (!isQuestionnaireFieldEnabled(field, sectionValues)) {
        return true;
      }
      if (!isQuestionnaireFieldRequired(field, sectionValues)) {
        return true;
      }
      const value = sectionValues[field.key];
      return Array.isArray(value) ? value.length > 0 : !!value;
    });
  });
  const assessmentMatricesValid = questionnaireConfigState.assessmentMatrices.every((section) =>
    section.questions.every((question) => !!(assessmentMatrixAnswers[section.key] || {})[question.key])
  );
  const step02QuestionnaireValid = activeQuestionBank.every((question) => {
    const answer = architectureAnswers.find((item) => item.id === question.id);
    return hasQuestionAnswerValue(answer?.answer);
  })
    && questionnaireSectionsValid
    && assessmentMatricesValid;
  const missingCommentForYes = architectureAnswers.some((item) => getQuestionAnswerValues(item.answer).includes('Y') && !item.comment.trim());
  const canSubmit = (isCreateNew ? !!form.projectName : !!form.projectId)
    && step02QuestionnaireValid
    && !missingCommentForYes;

  const handleReset = () => {
    // Reset all form states
    setForm({
      projectId: '', projectName: '', pm: '', pmItcode: '', 
      dtLead: '', dtLeadItcode: '', itLead: '', itLeadItcode: '',
      reviewScope: 'All', wsPhase: '', requestDesc: '',
    });
    setIsCreateNew(false);
    
    // Reset step 2 states
    setProjectType('');
    setProjectComplexity(0.5);
    setQuestionnaireSectionAnswers(buildDefaultQuestionnaireSectionAnswers(questionnaireSections));
    setQuestionnaireNote('');
    setAssessmentMatrixAnswers(buildDefaultAssessmentMatrixAnswers(questionnaireConfigState.assessmentMatrices));
    setArchitectureAnswers(defaultArchitectureAnswers(activeQuestionBank));
    
    // Reset request ID and step
    setRequestId(null);
    setStep(0);
    setIsNewlyCreated(false);
    
    // Clear URL parameter
    const url = new URL(window.location.href);
    url.searchParams.delete('id');
    window.history.replaceState({}, '', url.toString());
    
    messageApi.success('Form reset');
  };

  /* Whether project fields are read-only */
  // Editable when: Draft status AND current user is the requestor (createdBy)
  const isDraftAndOwner =
    existingRequest?.status === 'Draft' && !!user?.id && existingRequest?.createdBy === user.id;

  // Whether the current request is still in Draft status (or brand new)
  const isDraft = !existingRequest || existingRequest.status === 'Draft';

  // isViewMode: read-only when viewing someone else's request or a non-Draft request.
  // Explicitly NOT read-only when:
  //   - the request was just created in this session (isNewlyCreated), or
  //   - the loaded request is a Draft owned by current user (isDraftAndOwner)
  const isViewMode = !!requestId && !isNewlyCreated && !isDraftAndOwner;

  // Whether the request was originally loaded with a MSPO project (stable, based on server data).
  // Used to decide if the Project ID selector should remain editable.
  const originalProjectFromMspo = !!existingRequest?.projectSource;

  // If the project has a source (e.g. synced from MSPO), it is considered a MSPO project.
  // Tracks the *currently selected* project �?updates when the user picks a different project.
  const isProjectFromMspo = !isCreateNew && (
    currentProjectFromList ? !!currentProjectFromList.source : !!existingRequest?.projectSource
  );

  {"DT Lead / IT Lead are editable when:"}
  //   - brand new request in Create New mode, OR
  //   - existing Draft request owned by current user (isDraftAndOwner or isNewlyCreated)
  //   AND the project did NOT come from MSPO (MSPO project fields are always locked)
  const projectFieldsReadOnly = isViewMode || isProjectFromMspo || (!isCreateNew && !isDraftAndOwner && !isNewlyCreated);

  /* ── Render step content ── */
  const renderStep01 = () => (
    <>
      {/* Section: Select a MSPO project or create project */}
      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-4 text-gray-800">Select a MSPO project or create project</h3>

        {/* Project ID (MSPO) or Create New toggle */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1">
          {isDraftAndOwner && originalProjectFromMspo ? (
            // MSPO project in draft: allow re-selecting a different project
            <div>
              <FieldLabel label="Project ID" required />
              <Select
                value={form.projectId || undefined}
                onChange={handleProjectChange}
                placeholder="Type to search Project ID/Name"
                showSearch
                filterOption={false}
                onSearch={handleProjectSearch}
                loading={isProjectsLoading}
                allowClear
                virtual={false}
                className="w-full"
                notFoundContent={isProjectsLoading ? 'Searching...' : 'No projects found'}
                options={projects.map((p: any) => ({
                  label: `${p.projectId} - ${p.projectName}`,
                  value: p.projectId,
                }))}
              />
              {!form.projectId && (
                <div className="text-red-500 text-xs mt-1">Required</div>
              )}
            </div>
          ) : (isViewMode || !!requestId) ? (
            // Once a request exists (any status), Project ID is always read-only
            // Hide Create New / Select from MSPO buttons entirely
            <div>
              <FieldLabel label="Project ID" required />
              <Input
                value={form.projectId}
                disabled
                style={{ backgroundColor: '#f5f5f5' }}
              />
            </div>
          ) : !isCreateNew ? (
            // Create mode: show project selector with "Create New" button
            <div>
              <FieldLabel label="Project ID" required />
              <div className="flex gap-2">
                <Select
                  value={form.projectId || undefined}
                  onChange={handleProjectChange}
                  placeholder="Type to search Project ID/Name"
                  showSearch
                  filterOption={false}
                  onSearch={handleProjectSearch}
                  loading={isProjectsLoading}
                  allowClear
                  virtual={false}
                  className="flex-1"
                  notFoundContent={isProjectsLoading ? 'Searching...' : 'No projects found'}
                  options={projects.map((p: any) => ({
                    label: `${p.projectId} - ${p.projectName}`,
                    value: p.projectId,
                  }))}
                />
                <Button
                  icon={<PlusCircleOutlined />}
                  onClick={() => {
                    setIsCreateNew(true);
                    setForm((prev) => ({ ...prev, projectId: '', projectName: '', pm: '', pmItcode: '', dtLead: '', dtLeadItcode: '', itLead: '', itLeadItcode: '' }));
                  }}
                >
                  Create New
                </Button>
              </div>
              {!form.projectId && (
                <div className="text-red-500 text-xs mt-1">Required</div>
              )}
            </div>
          ) : (
            // Create new mode: show "Select from MSPO" button
            <div className="flex items-end">
              <Button
                onClick={() => {
                  setIsCreateNew(false);
                  setForm((prev) => ({ ...prev, projectId: '', projectName: '', pm: '', pmItcode: '', dtLead: '', dtLeadItcode: '', itLead: '', itLeadItcode: '' }));
                }}
              >
                Select from MSPO
              </Button>
            </div>
          )}
          <div />
        </div>

        {/* Project Name + PM */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 mt-3">
          <div>
            <FieldLabel label="Project Name" required />
            <Input
              value={form.projectName}
              onChange={(e) => set('projectName', e.target.value)}
              disabled={projectFieldsReadOnly}
              style={projectFieldsReadOnly ? { backgroundColor: '#f5f5f5' } : undefined}
            />
          </div>
          <div>
            <FieldLabel label="PM" required />
            {projectFieldsReadOnly ? (
              <Input value={form.pm || existingRequest?.pmName || ''} disabled style={{ backgroundColor: '#f5f5f5' }} />
            ) : (
              <ResourceAutoComplete
                value={form.pm}
                onChange={(val, resource) => {
                  setForm((prev) => ({ ...prev, pm: val, pmItcode: resource?.itcode || '' }));
                }}
                placeholder="Search by name or IT code"
              />
            )}
            {!form.pm && <div className="text-red-500 text-xs mt-1">Required</div>}
          </div>
        </div>

        {/* DT Lead + IT Lead */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 mt-3">
          <div>
            <FieldLabel label="Biz Analyst" required={!isProjectFromMspo} />
            {projectFieldsReadOnly ? (
              <Input value={form.dtLead || existingRequest?.dtLeadName || ''} disabled style={{ backgroundColor: '#f5f5f5' }} />
            ) : (
              <ResourceAutoComplete
                value={form.dtLead}
                onChange={(val, resource) => {
                  setForm((prev) => ({ ...prev, dtLead: val, dtLeadItcode: resource?.itcode || '' }));
                }}
                placeholder="Search by name or IT code"
              />
            )}
            {!isProjectFromMspo && !form.dtLead && <div className="text-red-500 text-xs mt-1">Required</div>}
          </div>
          <div>
            <FieldLabel label="IT Lead" required={!isProjectFromMspo} />
            {projectFieldsReadOnly ? (
              <Input value={form.itLead || existingRequest?.itLeadName || ''} disabled style={{ backgroundColor: '#f5f5f5' }} />
            ) : (
              <ResourceAutoComplete
                value={form.itLead}
                onChange={(val, resource) => {
                  setForm((prev) => ({ ...prev, itLead: val, itLeadItcode: resource?.itcode || '' }));
                }}
                placeholder="Search by name or IT code"
              />
            )}
            {!isProjectFromMspo && !form.itLead && <div className="text-red-500 text-xs mt-1">Required</div>}
          </div>
        </div>

        {/* Requestor + Request ID (always read-only) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 mt-3">
          <div>
            <FieldLabel label="Requestor" />
            <Input value={user?.id || ''} disabled style={{ backgroundColor: '#f5f5f5' }} />
          </div>
          <div>
            <FieldLabel label="Request ID" />
            <Input value={requestId || ''} disabled placeholder="Generated after saving" style={{ backgroundColor: '#f5f5f5' }} />
          </div>
        </div>
      </Card>

      {/* Section: Describe review scope */}
      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-4 text-gray-800">Describe review scope</h3>

        <div className="mb-3">
          <FieldLabel label="Review Scope" required />
          <Radio.Group
            value={form.reviewScope}
            onChange={(e) => set('reviewScope', e.target.value)}
            disabled={isViewMode}
          >
            <Radio value="All">All</Radio>
            <Radio value="Part of Project">Part of Project</Radio>
          </Radio.Group>
        </div>

        {form.reviewScope === 'Part of Project' && (
          <div className="mb-3">
            <FieldLabel label="WS Name / Phase Name" required />
            <Input
              value={form.wsPhase}
              onChange={(e) => set('wsPhase', e.target.value)}
              placeholder="All contents of the project or WS Name or Phase Name"
              disabled={isViewMode}
              style={isViewMode ? { backgroundColor: '#f5f5f5' } : undefined}
            />
          </div>
        )}

        <div className="text-xs text-gray-400 mb-1">* Default all contents of the project; Or WS Name; Or Phase Name</div>
        <div className="text-xs text-gray-400 mb-4">* After the description, submit and generate request id �?project id �?project name �?request name</div>

        <div>
          <FieldLabel label="Request Description" />
          <TextArea
            value={form.requestDesc}
            onChange={(e) => set('requestDesc', e.target.value)}
            autoSize={{ minRows: 4 }}
            disabled={isViewMode}
            style={isViewMode ? { backgroundColor: '#f5f5f5' } : undefined}
          />
        </div>
      </Card>

      {/* Buttons */}
      <div className="flex justify-center gap-3 mt-6">
        {isDraft ? (
          <>
            <Button
              type="primary"
              size="large"
              icon={<ArrowRightOutlined />}
              onClick={handleSaveAndNext}
              disabled={!canGoToStep2 || isSaving || saveDraftMutation.isPending}
              loading={isSaving || saveDraftMutation.isPending}
            >
              Save &amp; Next Step
            </Button>
            <Button size="large" icon={<UndoOutlined />} onClick={handleReset}>
              Reset
            </Button>
          </>
        ) : (
          <Button
            type="primary"
            size="large"
            icon={<ArrowRightOutlined />}
            onClick={() => setStep(1)}
          >
            Next Step
          </Button>
        )}
      </div>
    </>
  );

  const renderStep02 = () => (
    <>
      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-2">Questionnaire Step (Project Team)</h3>
        <p className="text-sm text-gray-600">
          Complete and submit the AVDM questionnaire on this page. This step is used to activate the relevant architecture concerns and viewpoints instead of documenting all possible concerns up front. After submission, the workflow is handed over to the review team for concern confirmation.
        </p>
      </Card>

      {/* AVDM questionnaire */}
      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-4 text-gray-800">Fill AVDM Questionnaire</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
          <div>
            <FieldLabel label={formCopy.projectTypeLabel} />
            <Select
              value={projectType || undefined}
              onChange={(value) => setProjectType(String(value || ''))}
              options={questionnaireConfigState.projectTypeOptions}
              allowClear
              disabled={isViewMode}
              placeholder="Select project type"
            />
          </div>
          <div>
            <FieldLabel label={formCopy.projectComplexityScoreLabel} required />
            <Input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={derivedProjectComplexity ?? projectComplexity}
              onChange={(e) => setProjectComplexity(Number(e.target.value || 0.5))}
              disabled={isViewMode || derivedProjectComplexity !== null}
              style={isViewMode ? { backgroundColor: '#f5f5f5' } : undefined}
            />
            {questionnaireConfigState.assessmentMatrices.length > 0 && (
              <div className="mt-1 text-xs text-slate-500">
                Calculated automatically from the backend-configured complexity assessment sections when all required answers are completed.
              </div>
            )}
          </div>
        </div>

        {(selectedProjectTypeProfile || projectTypeGuide.introduction.length > 0) && (
          <div className="mt-4 space-y-4">
            {selectedProjectTypeProfile && (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="text-sm font-semibold text-slate-800">Selected Project Type Guidance</div>
                <div className="mt-1 text-sm text-slate-600">{selectedProjectTypeProfile.description}</div>
                {selectedProjectTypeProfile.artifactSelections.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedProjectTypeProfile.artifactSelections.map((selection) => (
                      <span
                        key={`${selectedProjectTypeProfile.value}-${selection.artifactKey}`}
                        className={`rounded border px-2 py-1 text-xs font-medium ${projectTypeStatusClass(selection.status)}`}
                      >
                        {selection.artifactLabel}: {selection.status}
                      </span>
                    ))}
                  </div>
                )}
                {selectedProjectTypeProfile.typicalPatterns.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Typical Patterns</div>
                    <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
                      {selectedProjectTypeProfile.typicalPatterns.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                )}
                {selectedProjectTypeProfile.typicalRisks.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Typical Risks</div>
                    <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
                      {selectedProjectTypeProfile.typicalRisks.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <details className="rounded-md border border-slate-200 bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-800">
                {projectTypeGuide.title || 'Project Type Guidance'}
              </summary>
              <div className="mt-4 space-y-4 text-sm text-slate-600">
                {projectTypeGuide.introduction.map((item) => (
                  <p key={item}>{item}</p>
                ))}

                {projectTypeGuide.objectives.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">Objectives</div>
                    <div className="mt-2 space-y-2">
                      {projectTypeGuide.objectives.map((item) => (
                        <div key={item.title}>
                          <div className="font-medium text-slate-800">{item.title}</div>
                          <div>{item.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(projectTypeGuide.scopeIntro || projectTypeGuide.scopeProjectTypes.length > 0 || projectTypeGuide.scopeNote) && (
                  <div>
                    <div className="font-semibold text-slate-800">Scope</div>
                    {projectTypeGuide.scopeIntro && <div className="mt-2">{projectTypeGuide.scopeIntro}</div>}
                    {projectTypeGuide.scopeProjectTypes.length > 0 && (
                      <ul className="mt-2 list-disc pl-5">
                        {projectTypeGuide.scopeProjectTypes.map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    )}
                    {projectTypeGuide.scopeNote && <div className="mt-2">{projectTypeGuide.scopeNote}</div>}
                  </div>
                )}

                {projectTypeGuide.corePrinciples.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">Core Principles</div>
                    <div className="mt-2 space-y-2">
                      {projectTypeGuide.corePrinciples.map((item) => (
                        <div key={item.title}>
                          <div className="font-medium text-slate-800">{item.title}</div>
                          <div>{item.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {projectTypeGuide.governanceBoundary.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">EA Governance Boundary</div>
                    <ul className="mt-2 list-disc pl-5">
                      {projectTypeGuide.governanceBoundary.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                )}

                {projectTypeGuide.recommendedUsage.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">Recommended Usage</div>
                    <ul className="mt-2 list-disc pl-5">
                      {projectTypeGuide.recommendedUsage.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                )}

                {projectTypeGuide.artifactSelectionIntro.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">Architecture Artifact Selection</div>
                    <div className="mt-2 space-y-2">
                      {projectTypeGuide.artifactSelectionIntro.map((item) => <p key={item}>{item}</p>)}
                    </div>
                  </div>
                )}

                {questionnaireConfigState.projectTypeProfiles.length > 0 && (
                  <div className="overflow-x-auto rounded border border-slate-200">
                    <table className="min-w-full border-collapse text-xs sm:text-sm">
                      <thead className="bg-slate-50 text-slate-700">
                        <tr>
                          <th className="border-b border-slate-200 px-3 py-2 text-left">Project Type</th>
                          <th className="border-b border-slate-200 px-3 py-2 text-left">Description</th>
                          <th className="border-b border-slate-200 px-3 py-2 text-left">Artifacts</th>
                          <th className="border-b border-slate-200 px-3 py-2 text-left">Patterns</th>
                          <th className="border-b border-slate-200 px-3 py-2 text-left">Risks</th>
                        </tr>
                      </thead>
                      <tbody>
                        {questionnaireConfigState.projectTypeProfiles.map((profile) => (
                          <tr key={profile.value}>
                            <td className="border-b border-slate-100 px-3 py-2 align-top font-medium text-slate-800">{profile.label}</td>
                            <td className="border-b border-slate-100 px-3 py-2 align-top">{profile.description}</td>
                            <td className="border-b border-slate-100 px-3 py-2 align-top">
                              <div className="flex flex-wrap gap-2">
                                {profile.artifactSelections.map((selection) => (
                                  <span
                                    key={`${profile.value}-${selection.artifactKey}`}
                                    className={`rounded border px-2 py-1 text-xs font-medium ${projectTypeStatusClass(selection.status)}`}
                                  >
                                    {selection.artifactLabel}: {selection.status}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="border-b border-slate-100 px-3 py-2 align-top">
                              {profile.typicalPatterns.length > 0 ? profile.typicalPatterns.join(', ') : '-'}
                            </td>
                            <td className="border-b border-slate-100 px-3 py-2 align-top">
                              {profile.typicalRisks.length > 0 ? profile.typicalRisks.join(', ') : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {projectTypeGuide.legend.length > 0 && (
                  <div>
                    <div className="font-semibold text-slate-800">Legend</div>
                    <ul className="mt-2 list-disc pl-5">
                      {projectTypeGuide.legend.map((item) => <li key={item.symbol}>{item.symbol}: {item.meaning}</li>)}
                    </ul>
                  </div>
                )}

                {projectTypeGuide.note && (
                  <div className="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-slate-700">
                    {projectTypeGuide.note}
                  </div>
                )}
              </div>
            </details>
          </div>
        )}

        {questionnaireSections.map((section) => {
          const sectionValues = questionnaireSectionAnswers[section.key] || {};
          return (
            <div key={section.key} className="mt-5">
              <div className="mb-2 text-sm font-semibold text-gray-800">{section.title}</div>
              {section.description && <div className="mb-2 text-xs text-gray-500">{section.description}</div>}
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {section.fields.map((field) => {
                  const enabled = isQuestionnaireFieldEnabled(field, sectionValues);
                  const required = enabled && isQuestionnaireFieldRequired(field, sectionValues);
                  const options = field.optionsSource ? (rangeOptionSourceMap[field.optionsSource] || field.options || []) : field.options || [];
                  const stringValue = getQuestionnaireStringValue(sectionValues[field.key]);
                  const arrayValue = getQuestionnaireArrayValue(sectionValues[field.key]);
                  return (
                    <div key={`${section.key}-${field.key}`}>
                      <FieldLabel label={field.label} required={required} />
                      {field.control === 'radio' ? (
                        <Radio.Group
                          value={stringValue}
                          onChange={(event) => updateQuestionnaireSectionField(section.key, field.key, event.target.value)}
                          disabled={isViewMode || !enabled}
                        >
                          {options.map((option) => (
                            <Radio key={`${section.key}-${field.key}-${option.value}`} value={option.value}>{option.label}</Radio>
                          ))}
                        </Radio.Group>
                      ) : field.control === 'multiselect' ? (
                        <Select
                          mode="multiple"
                          value={arrayValue}
                          onChange={(value) => updateQuestionnaireSectionField(section.key, field.key, (value || []).map(String))}
                          disabled={isViewMode || !enabled}
                          allowClear
                          options={options}
                          placeholder={field.placeholder}
                        />
                      ) : field.control === 'text' ? (
                        <Input
                          value={stringValue}
                          onChange={(event) => updateQuestionnaireSectionField(section.key, field.key, event.target.value)}
                          disabled={isViewMode || !enabled}
                          placeholder={field.placeholder}
                        />
                      ) : field.control === 'textarea' ? (
                        <TextArea
                          value={stringValue}
                          onChange={(event) => updateQuestionnaireSectionField(section.key, field.key, event.target.value)}
                          disabled={isViewMode || !enabled}
                          placeholder={field.placeholder}
                          rows={3}
                        />
                      ) : (
                        <Select
                          value={stringValue || undefined}
                          onChange={(value) => updateQuestionnaireSectionField(section.key, field.key, String(value || ''))}
                          disabled={isViewMode || !enabled}
                          allowClear
                          options={options}
                          placeholder={field.placeholder}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        <div className="mt-4">
          <FieldLabel label={formCopy.questionnaireNotesLabel} />
          <TextArea
            value={questionnaireNote}
            onChange={(e) => setQuestionnaireNote(e.target.value)}
            rows={3}
            disabled={isViewMode}
            style={isViewMode ? { backgroundColor: '#f5f5f5' } : undefined}
          />
        </div>

        {questionnaireConfigState.assessmentMatrices.map((section) => {
          const sectionScore = calculateAssessmentMatrixSectionScore(section);
          return (
            <div key={section.key} className="mt-5">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-800">{section.title}</div>
                  {section.description && <div className="mt-1 text-xs text-gray-500">{section.description}</div>}
                </div>
                {sectionScore.maximum > 0 && (
                  <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600">
                    Score: {sectionScore.earned} / {sectionScore.maximum}
                  </div>
                )}
              </div>
              <div className="space-y-3">
                {section.questions.map((question) => (
                  <div key={`${section.key}-${question.key}`} className="border border-gray-200 rounded-md p-3">
                    <div className="text-sm font-medium">{question.title}</div>
                    {question.helperText && (
                      <div className="mt-1 text-xs text-gray-500">
                        {question.helperText}
                        {question.weight ? ` Weight x${question.weight}` : ''}
                      </div>
                    )}
                    <div className="mt-2">
                      {question.control === 'select' ? (
                        <Select
                          value={(assessmentMatrixAnswers[section.key] || {})[question.key] || undefined}
                          onChange={(value) => setAssessmentMatrixAnswers((previous) => ({
                            ...previous,
                            [section.key]: {
                              ...(previous[section.key] || {}),
                              [question.key]: String(value || ''),
                            },
                          }))}
                          disabled={isViewMode}
                          allowClear
                          options={question.options}
                        />
                      ) : (
                        <Radio.Group
                          value={(assessmentMatrixAnswers[section.key] || {})[question.key] || ''}
                          onChange={(event) => setAssessmentMatrixAnswers((previous) => ({
                            ...previous,
                            [section.key]: {
                              ...(previous[section.key] || {}),
                              [question.key]: event.target.value,
                            },
                          }))}
                          disabled={isViewMode}
                        >
                          {question.options.map((option) => (
                            <Radio key={`${section.key}-${question.key}-${option.value}`} value={option.value}>
                              {option.label}
                              {typeof option.score === 'number' ? ` (${option.score})` : ''}
                            </Radio>
                          ))}
                        </Radio.Group>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {activeQuestionnaireCategories
          .filter((category) => activeQuestionBank.some((question) => question.category === category.key))
          .map((category) => (
          <div key={category.key} className="mt-5">
            <div className="mb-2 text-sm font-semibold text-gray-800">{category.label}</div>
            {category.description && (
              <div className="mb-3 text-xs text-gray-500">{category.description}</div>
            )}
            <div className="space-y-3">
              {activeQuestionBank
                .filter((q) => q.category === category.key)
                .map((q, questionIndex) => {
                  const answer = architectureAnswers.find((item) => item.id === q.id);
                  const questionOptions = resolveQuestionOptions(q);
                  const concernHints = concernMappingConfigState.questionConcernMappings
                    .filter((mapping) => mapping.questionId === q.id)
                    .flatMap((mapping) => mapping.hints || []);
                  return (
                    <div key={q.id} className="border border-gray-200 rounded-md p-3">
                      <div className="text-sm font-medium">{questionIndex + 1}. {q.text}</div>
                      {(q.designIntent || concernHints.length > 0) && (
                        <div className="mt-1 text-xs text-gray-500">
                          {q.designIntent && <div>{q.designIntent}</div>}
                          {concernHints.length > 0 && (
                            <div>{formCopy.concernActivationHintPrefix} {Array.from(new Set(concernHints)).join(', ')}</div>
                          )}
                        </div>
                      )}
                      <div className="mt-2">
                        {q.control === 'radio' ? (
                          <Radio.Group
                            value={getQuestionAnswerStringValue(answer?.answer)}
                            onChange={(e) => setArchitectureAnswers((prev) => prev.map((item) => (
                              item.id === q.id ? { ...item, answer: String(e.target.value || '') } : item
                            )))}
                            disabled={isViewMode}
                          >
                            {questionOptions.map((option) => (
                              <Radio key={`${q.id}-${option.value}`} value={option.value}>{option.label}</Radio>
                            ))}
                          </Radio.Group>
                        ) : q.control === 'multiselect' ? (
                          <Select
                            mode="multiple"
                            value={getQuestionAnswerArrayValue(answer?.answer)}
                            onChange={(value) => setArchitectureAnswers((prev) => prev.map((item) => (
                              item.id === q.id ? { ...item, answer: (value || []).map(String) } : item
                            )))}
                            disabled={isViewMode}
                            allowClear
                            options={questionOptions}
                            placeholder={q.placeholder}
                          />
                        ) : q.control === 'text' ? (
                          <Input
                            value={getQuestionAnswerStringValue(answer?.answer)}
                            onChange={(e) => setArchitectureAnswers((prev) => prev.map((item) => (
                              item.id === q.id ? { ...item, answer: e.target.value } : item
                            )))}
                            disabled={isViewMode}
                            placeholder={q.placeholder}
                          />
                        ) : q.control === 'textarea' ? (
                          <TextArea
                            value={getQuestionAnswerStringValue(answer?.answer)}
                            onChange={(e) => setArchitectureAnswers((prev) => prev.map((item) => (
                              item.id === q.id ? { ...item, answer: e.target.value } : item
                            )))}
                            disabled={isViewMode}
                            placeholder={q.placeholder}
                            rows={3}
                          />
                        ) : (
                          <Select
                            value={getQuestionAnswerStringValue(answer?.answer) || undefined}
                            onChange={(value) => setArchitectureAnswers((prev) => prev.map((item) => (
                              item.id === q.id ? { ...item, answer: String(value || '') } : item
                            )))}
                            disabled={isViewMode}
                            allowClear
                            options={questionOptions}
                            placeholder={q.placeholder}
                          />
                        )}
                      </div>
                      <div className="mt-2">
                        <Input
                          value={answer?.comment || ''}
                          onChange={(e) => setArchitectureAnswers((prev) => prev.map((item) => (
                            item.id === q.id ? { ...item, comment: e.target.value } : item
                          )))}
                          disabled={isViewMode}
                          placeholder="Comments (optional; required when answer is Y)"
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        ))}
      </Card>

      {/* Buttons */}
      <div className="flex justify-center gap-3 mt-6">
        {isDraft ? (
          <>
            <Tooltip
              title={
                !canSubmit
                  ? !step02QuestionnaireValid
                    ? 'Please select Project Scale, Project Change Scope, and answer all categorized questions'
                    : missingCommentForYes
                      ? 'Please fill comments for every Y answer'
                    : undefined
                  : undefined
              }
            >
              <Button
                type="primary"
                size="large"
                icon={<ArrowRightOutlined />}
                onClick={() => setShowConfirmModal(true)}
                disabled={!canSubmit}
              >
                Submit Questionnaire to Review Team
              </Button>
            </Tooltip>
            <Button
              size="large"
              icon={<SaveOutlined />}
              onClick={() => {
                questionnaireMutation.mutate({
                  projectType: projectType || null,
                  projectComplexity: derivedProjectComplexity ?? projectComplexity,
                  questionnaire: {
                    ...questionnaireSectionAnswers,
                    assessmentMatrices: assessmentMatrixAnswers,
                    note: questionnaireNote,
                    architectureAnswers,
                    activatedConcernKeys: buildActivatedConcernKeys(),
                    checkpoint1,
                    checkpoint2,
                    checkpoint3,
                  },
                  answers: buildQuestionnaireRiskAnswers(),
                  status: 'draft',
                  operator: user?.id || 'system',
                }, {
                  onSuccess: () => {
                    messageApi.success('Questionnaire saved as draft');
                  },
                });
              }}
              loading={questionnaireMutation.isPending || isSaving || saveDraftMutation.isPending}
            >
              Save as Draft
            </Button>
          </>
        ) : (
          <>
            <Button
              type="primary"
              size="large"
              icon={<ArrowRightOutlined />}
              onClick={() => setStep(2)}
            >
              Continue to Review Team Step
            </Button>
            {requestId && (
              <Button
                size="large"
                onClick={() => router.push(`/request/${requestId}`)}
              >
                View Request Detail
              </Button>
            )}
          </>
        )}
      </div>

      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-2">Next Step Handoff</h3>
        <p className="text-sm text-gray-600">
          After questionnaire submission, the review team will confirm the project concerns as the next workflow step.
        </p>
      </Card>
    </>
  );

  const renderStep03 = () => (
    <>
      <Card size="small" className="shadow-sm" style={{ marginBottom: 15 }}>
        <h3 className="font-semibold text-sm mb-2">Confirm Concerns (Review Team)</h3>
        <p className="text-sm text-gray-600">
          This step is executed by the review team. They will confirm concern requirements after questionnaire submission.
        </p>
      </Card>

      <div className="flex justify-center gap-3 mt-6">
        {requestId ? (
          <Button
            type="primary"
            size="large"
            icon={<ArrowRightOutlined />}
            onClick={() => router.push(`/request/${requestId}`)}
          >
            Go to Request Detail for Concern Confirmation
          </Button>
        ) : (
          <Button size="large" onClick={() => setStep(1)}>Back to Questionnaire</Button>
        )}
      </div>
    </>
  );

  const stepContents = [renderStep01, renderStep02, renderStep03];

  return (
    <div className="min-h-[calc(100vh-56px)] bg-[#f0f2f5]">
      {contextHolder}

      {/* Page title banner */}
      <div className="bg-gradient-to-r from-[#4096FF] to-[#1677FF] text-white px-4 md:px-8 py-3 flex items-center gap-2 shadow-sm">
        <HomeOutlined className="cursor-pointer" onClick={() => router.push('/')} />
        <span className="text-base font-semibold tracking-wide">
          {requestId
            ? `Request Name : ${requestId}-${form.projectId}-${form.projectName}`
            : 'Create A Request'}
        </span>
      </div>

      <div className="max-w-[1200px] mx-auto px-4 md:px-8 py-6">
        {/* Error */}
        {(saveDraftMutation.isError || submitMutation.isError) && (
          <Alert type="error" showIcon title="Failed to save request. Please try again." className="mb-4" />
        )}

        <div className="flex flex-col md:flex-row gap-6 md:gap-8">
          {/* Steps navigation */}
          <div className={isMdUp ? 'w-56 shrink-0' : ''}>
            <div className={isMdUp ? 'bg-white rounded-lg shadow-sm p-5 sticky top-20' : 'bg-white rounded-lg shadow-sm p-4 overflow-x-auto'}>
              <Steps
                current={step}
                orientation={isMdUp ? 'vertical' : 'horizontal'}
                items={STEPS.map((s, i) => ({
                  title: (
                    <span className="text-sm font-semibold leading-snug">
                      {String(i + 1).padStart(2, '0')}. {s.title}
                    </span>
                  ),
                }))}
                onChange={(val) => {
                  if (val < step) setStep(val);
                  else if (val === 1 && canGoToStep2) setStep(val);
                  else if (val === 2 && !!requestId) setStep(val);
                }}
                className="create-request-steps"
              />
            </div>
          </div>

          {/* Step content */}
          <div className="flex-1 min-w-0">
            {stepContents[step]()}
          </div>
        </div>
      </div>

      {/* Confirm to Submit Modal */}
      <Modal
        title="Submit Questionnaire (Project Team)"
        open={showConfirmModal}
        onCancel={() => setShowConfirmModal(false)}
        footer={
          <Space>
            <Button onClick={() => setShowConfirmModal(false)}>Cancel</Button>
            <Button type="primary" onClick={handleConfirmSubmit} loading={submitMutation.isPending}>
              Yes
            </Button>
          </Space>
        }
      >
        <div>
          <div className="mb-1 text-sm">Comments</div>
          <TextArea
            value={submitComments}
            onChange={(e) => setSubmitComments(e.target.value)}
            rows={4}
          />
        </div>
      </Modal>
    </div>
  );
}

