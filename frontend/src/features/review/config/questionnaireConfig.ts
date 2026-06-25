export type YesNo = '' | 'Yes' | 'No';

export type QuestionnaireCategoryKey = string;

export type QuestionnaireCategoryGroupKey = 'scale_overall' | 'complexity_overall' | 'change' | 'architecture_type';

export type CategoryConfig = {
  key: QuestionnaireCategoryKey;
  label: string;
  description?: string;
  group?: QuestionnaireCategoryGroupKey;
};

export type QuestionControl = 'radio' | 'select' | 'multiselect' | 'text' | 'textarea';

export type QuestionSourceScope = 'question_bank' | 'questionnaire_section' | 'assessment_matrix';

export type QuestionConfig = {
  id: number;
  questionKey?: string;
  text: string;
  category: QuestionnaireCategoryKey;
  designIntent?: string;
  control: QuestionControl;
  options?: Option[];
  optionsSource?: string;
  placeholder?: string;
  sourceScope?: QuestionSourceScope;
  sourceRef?: string;
};

export type QuestionnaireFormCopy = {
  projectTypeLabel: string;
  projectComplexityScoreLabel: string;
  projectScaleTitle: string;
  applicationsInScopeLabel: string;
  hasExternalSystemsLabel: string;
  externalSystemsCountLabel: string;
  changeScopeTitle: string;
  hasNewApplicationsLabel: string;
  newApplicationsCountLabel: string;
  modifiedApplicationsCountLabel: string;
  complexitySectionTitle: string;
  dataCenterCountLabel: string;
  cloudRegionScopeLabel: string;
  crossBorderDataLabel: string;
  techStackKindsCountLabel: string;
  integrationTechKindsCountLabel: string;
  questionnaireNotesLabel: string;
  yesLabel: string;
  noLabel: string;
  positiveAnswerLabel: string;
  negativeAnswerLabel: string;
  concernActivationHintPrefix: string;
};

export type ConcernActivationCondition = {
  source: string;
  equals?: string | number | boolean;
  in?: Array<string | number | boolean>;
  notEquals?: string | number | boolean;
};

export type ConcernActivationRule = {
  id: string;
  description: string;
  concernScores: ConcernScoreMapping[];
  concernKeys?: string[];
  all?: ConcernActivationCondition[];
  any?: ConcernActivationCondition[];
  severity?: number;
  likelihood?: number;
  score?: number;
};

export type ConcernScoreMapping = {
  concernKey: string;
  score: number;
  severity?: number;
  likelihood?: number;
  note?: string;
};

export type QuestionConcernMapping = {
  questionId: number;
  answer: string;
  concernScores: ConcernScoreMapping[];
  hints?: string[];
};

export type Option = {
  label: string;
  value: string;
  score?: number;
};

export type AnswerTypeConfig = {
  key: string;
  name: string;
  storageKind: string;
  widget: QuestionControl | string;
  allowsMultiple: boolean;
  allowsFreeText: boolean;
  description?: string;
};

export type AnswerOptionSetConfig = {
  key: string;
  name: string;
  description?: string;
  isShared?: boolean;
  sortOrder?: number;
  options: Option[];
};

export type AssessmentMatrixQuestion = {
  id?: number;
  key: string;
  title: string;
  helperText?: string;
  weight?: number;
  control?: 'radio' | 'select';
  options: Option[];
};

export type AssessmentMatrixSection = {
  key: string;
  title: string;
  description?: string;
  questions: AssessmentMatrixQuestion[];
};

export type QuestionnaireSectionFieldCondition = {
  field: string;
  equals?: string;
  in?: string[];
  notEquals?: string;
};

export type QuestionnaireSectionField = {
  key: string;
  label: string;
  control: 'radio' | 'select' | 'multiselect' | 'text' | 'textarea';
  options?: Option[];
  optionsSource?: string;
  required?: boolean;
  enabledWhen?: QuestionnaireSectionFieldCondition[];
  requiredWhen?: QuestionnaireSectionFieldCondition[];
  clearWhenDisabled?: boolean;
  placeholder?: string;
};

export type QuestionnaireFieldValue = string | string[];

export type QuestionnaireSection = {
  key: string;
  title: string;
  description?: string;
  fields: QuestionnaireSectionField[];
};

export type ProjectTypeArtifactStatus = 'Mandatory' | 'Recommended' | 'Optional' | 'Not Required';

export type ProjectTypeGuideItem = {
  title: string;
  description: string;
};

export type ProjectTypeGuideLegendItem = {
  symbol: string;
  meaning: string;
};

export type ProjectTypeArtifactSelection = {
  artifactKey: string;
  artifactLabel: string;
  status: ProjectTypeArtifactStatus;
};

export type ProjectTypeProfile = {
  value: string;
  label: string;
  description: string;
  artifactSelections: ProjectTypeArtifactSelection[];
  typicalPatterns: string[];
  typicalRisks: string[];
};

export type ProjectTypeGuide = {
  title: string;
  introduction: string[];
  objectives: ProjectTypeGuideItem[];
  scopeIntro: string;
  scopeProjectTypes: string[];
  scopeNote: string;
  corePrinciples: ProjectTypeGuideItem[];
  governanceBoundary: string[];
  recommendedUsage: string[];
  artifactSelectionIntro: string[];
  legend: ProjectTypeGuideLegendItem[];
  note: string;
};

export type ProjectScaleSection = {
  applicationsInScope: string;
  hasExternalSystems: YesNo;
  externalSystemsCount: string;
};

export type ChangeScopeSection = {
  hasNewApplications: YesNo;
  newApplicationsCount: string;
  modifiedApplicationsCount: string;
};

export type ComplexitySection = {
  dataCenterCount: string;
  cloudRegionScope: string;
  hasCrossBorderDataFlow: YesNo;
  techStackKindsCount: string;
  integrationTechKindsCount: string;
};

export const defaultProjectScaleSection = (): ProjectScaleSection => ({
  applicationsInScope: '',
  hasExternalSystems: '',
  externalSystemsCount: '',
});

export const defaultChangeScopeSection = (): ChangeScopeSection => ({
  hasNewApplications: '',
  newApplicationsCount: '',
  modifiedApplicationsCount: '',
});

export const defaultComplexitySection = (): ComplexitySection => ({
  dataCenterCount: '',
  cloudRegionScope: '',
  hasCrossBorderDataFlow: '',
  techStackKindsCount: '',
  integrationTechKindsCount: '',
});

export type QuestionnaireConfig = {
  questionnaireSections: QuestionnaireSection[];
  questionnaireCategories: CategoryConfig[];
  questionBank: QuestionConfig[];
  answerTypes: AnswerTypeConfig[];
  optionSets: AnswerOptionSetConfig[];
  projectTypeOptions: Option[];
  projectTypeGuide: ProjectTypeGuide;
  assessmentMatrices: AssessmentMatrixSection[];
  projectTypeProfiles: ProjectTypeProfile[];
  applicationCountRangeOptions: Option[];
  externalSystemCountRangeOptions: Option[];
  newApplicationCountRangeOptions: Option[];
  modifiedApplicationCountRangeOptions: Option[];
  dataCenterCountRangeOptions: Option[];
  cloudRegionScopeOptions: Option[];
  techStackKindsCountRangeOptions: Option[];
  integrationTechKindsCountRangeOptions: Option[];
};

export type ConcernMappingConfig = {
  questionConcernMappings: QuestionConcernMapping[];
  concernActivationRules: ConcernActivationRule[];
};

export const defaultQuestionnaireFormCopy: QuestionnaireFormCopy = {
  projectTypeLabel: 'Technical Architecture Type',
  projectComplexityScoreLabel: 'Project Complexity (0~1)',
  projectScaleTitle: 'Project Scale',
  applicationsInScopeLabel: 'How many applications are in scope?',
  hasExternalSystemsLabel: 'Does it involve external systems?',
  externalSystemsCountLabel: 'How many external systems are involved?',
  changeScopeTitle: 'Change Scope',
  hasNewApplicationsLabel: 'Will there be new applications?',
  newApplicationsCountLabel: 'How many new applications?',
  modifiedApplicationsCountLabel: 'How many applications will be modified?',
  complexitySectionTitle: 'Project Complexity',
  dataCenterCountLabel: 'How many data centers are involved?',
  cloudRegionScopeLabel: 'How many clouds/regions are involved?',
  crossBorderDataLabel: 'Does this involve cross-border data?',
  techStackKindsCountLabel: 'How many technology stacks are involved?',
  integrationTechKindsCountLabel: 'How many integration technologies are involved?',
  questionnaireNotesLabel: 'Questionnaire Notes',
  yesLabel: 'Yes',
  noLabel: 'No',
  positiveAnswerLabel: 'Y',
  negativeAnswerLabel: 'N',
  concernActivationHintPrefix: 'Concern activation hint:',
};

export const emptyProjectTypeGuide: ProjectTypeGuide = {
  title: '',
  introduction: [],
  objectives: [],
  scopeIntro: '',
  scopeProjectTypes: [],
  scopeNote: '',
  corePrinciples: [],
  governanceBoundary: [],
  recommendedUsage: [],
  artifactSelectionIntro: [],
  legend: [],
  note: '',
};

export const emptyQuestionnaireConfig: QuestionnaireConfig = {
  questionnaireSections: [],
  questionnaireCategories: [],
  questionBank: [],
  answerTypes: [],
  optionSets: [],
  projectTypeOptions: [],
  projectTypeGuide: emptyProjectTypeGuide,
  assessmentMatrices: [],
  projectTypeProfiles: [],
  applicationCountRangeOptions: [],
  externalSystemCountRangeOptions: [],
  newApplicationCountRangeOptions: [],
  modifiedApplicationCountRangeOptions: [],
  dataCenterCountRangeOptions: [],
  cloudRegionScopeOptions: [],
  techStackKindsCountRangeOptions: [],
  integrationTechKindsCountRangeOptions: [],
};

export const emptyConcernMappingConfig: ConcernMappingConfig = {
  questionConcernMappings: [],
  concernActivationRules: [],
};

const QUESTIONNAIRE_CATEGORY_KEY_ALIASES: Record<string, QuestionnaireCategoryKey> = {
  business: 'business_change',
  application: 'application_change',
  data: 'data_change',
  data_chnage: 'data_change',
  technology: 'technology_change',
  compliance: 'compliance_change',
  other: 'other_change',
  other_chnage: 'other_change',
  change_scope: 'change_scale',
};

const categoryGroupOrder: QuestionnaireCategoryGroupKey[] = ['scale_overall', 'complexity_overall', 'change', 'architecture_type'];

function deriveCategoryGroup(key: QuestionnaireCategoryKey): QuestionnaireCategoryGroupKey | undefined {
  if (['project_scale', 'change_scale', 'project_resource_and_size'].includes(key)) {
    return 'scale_overall';
  }
  if (['technical_complexity', 'data_complexity', 'compliance_complexity', 'requirement_complexity', 'solution_complexity', 'security_complexity'].includes(key)) {
    return 'complexity_overall';
  }
  if (['business_change', 'application_change', 'data_change', 'technology_change', 'compliance_change', 'security_change', 'other_change'].includes(key)) {
    return 'change';
  }
  if (['technical_architecture_type', 'application_architecture_type', 'data_architecture_type', 'business_architecture_type', 'security_architecture_type'].includes(key)) {
    return 'architecture_type';
  }
  return undefined;
}

function normalizeCategoryGroup(raw: unknown, key: QuestionnaireCategoryKey): QuestionnaireCategoryGroupKey | undefined {
  if (raw === 'scale_overall' || raw === 'complexity_overall' || raw === 'change' || raw === 'architecture_type') {
    return raw;
  }
  return deriveCategoryGroup(key);
}

function normalizeCategoryKey(raw: unknown): QuestionnaireCategoryKey {
  const key = typeof raw === 'string' ? raw : String(raw ?? '');
  return QUESTIONNAIRE_CATEGORY_KEY_ALIASES[key] ?? key;
}

const toConcernScores = (concernKeys: string[], score = 8): ConcernScoreMapping[] =>
  concernKeys.map((concernKey) => ({ concernKey, score }));

const toStringArray = (raw: any): string[] => (
  Array.isArray(raw) ? raw.filter((item) => typeof item === 'string').map(String) : []
);

function normalizeGuideItems(raw: any): ProjectTypeGuideItem[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.title === 'string' && typeof item.description === 'string')
      .map((item: any) => ({
        title: String(item.title),
        description: String(item.description),
      }))
    : [];
}

function normalizeGuideLegend(raw: any): ProjectTypeGuideLegendItem[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.symbol === 'string' && typeof item.meaning === 'string')
      .map((item: any) => ({
        symbol: String(item.symbol),
        meaning: String(item.meaning),
      }))
    : [];
}

function normalizeArtifactSelections(raw: any): ProjectTypeArtifactSelection[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.artifactKey === 'string' && typeof item.artifactLabel === 'string' && typeof item.status === 'string')
      .map((item: any) => ({
        artifactKey: String(item.artifactKey),
        artifactLabel: String(item.artifactLabel),
        status: String(item.status) as ProjectTypeArtifactStatus,
      }))
    : [];
}

function normalizeProjectTypeProfiles(raw: any): ProjectTypeProfile[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.value === 'string' && typeof item.label === 'string')
      .map((item: any) => ({
        value: String(item.value),
        label: String(item.label),
        description: typeof item.description === 'string' ? item.description : '',
        artifactSelections: normalizeArtifactSelections(item.artifactSelections),
        typicalPatterns: toStringArray(item.typicalPatterns),
        typicalRisks: toStringArray(item.typicalRisks),
      }))
    : [];
}

function normalizeOptions(raw: any): Option[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.label === 'string' && typeof item.value === 'string')
      .map((item: any) => ({
        label: String(item.label),
        value: String(item.value),
        score: Number.isFinite(Number(item.score)) ? Number(item.score) : undefined,
      }))
    : [];
}

function normalizeAnswerTypes(raw: any): AnswerTypeConfig[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.key === 'string')
      .map((item: any) => ({
        key: String(item.key),
        name: String(item.name || item.label || item.key),
        storageKind: String(item.storageKind || 'single_choice'),
        widget: String(item.widget || item.key),
        allowsMultiple: Boolean(item.allowsMultiple),
        allowsFreeText: Boolean(item.allowsFreeText),
        description: typeof item.description === 'string' ? item.description : undefined,
      }))
    : [];
}

function normalizeOptionSets(raw: any): AnswerOptionSetConfig[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.key === 'string')
      .map((item: any) => ({
        key: String(item.key),
        name: String(item.name || item.label || item.key),
        description: typeof item.description === 'string' ? item.description : undefined,
        isShared: item.isShared !== false,
        sortOrder: Number.isFinite(Number(item.sortOrder)) ? Number(item.sortOrder) : undefined,
        options: normalizeOptions(item.options),
      }))
    : [];
}

function normalizeAssessmentMatrices(raw: any): AssessmentMatrixSection[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.key === 'string' && typeof item.title === 'string')
      .map((item: any) => ({
        key: String(item.key),
        title: String(item.title),
        description: typeof item.description === 'string' ? item.description : undefined,
        questions: Array.isArray(item.questions)
          ? item.questions
            .filter((question: any) => question && typeof question.key === 'string' && typeof question.title === 'string')
            .map((question: any) => ({
              id: Number.isFinite(Number(question.id)) ? Number(question.id) : undefined,
              key: String(question.key),
              title: String(question.title),
              helperText: typeof question.helperText === 'string' ? question.helperText : undefined,
              weight: Number.isFinite(Number(question.weight)) ? Number(question.weight) : undefined,
              control: question.control === 'select' ? 'select' : 'radio',
              options: normalizeOptions(question.options),
            }))
          : [],
      }))
    : [];
}

function normalizeQuestionnaireSectionConditions(raw: any): QuestionnaireSectionFieldCondition[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.field === 'string')
      .map((item: any) => ({
        field: String(item.field),
        equals: typeof item.equals === 'string' ? item.equals : undefined,
        in: Array.isArray(item.in) ? item.in.filter((value: any) => typeof value === 'string').map(String) : undefined,
        notEquals: typeof item.notEquals === 'string' ? item.notEquals : undefined,
      }))
    : [];
}

function normalizeQuestionnaireSections(raw: any): QuestionnaireSection[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => item && typeof item.key === 'string' && typeof item.title === 'string')
      .map((item: any) => ({
        key: String(item.key),
        title: String(item.title),
        description: typeof item.description === 'string' ? item.description : undefined,
        fields: Array.isArray(item.fields)
          ? item.fields
            .filter((field: any) => field && typeof field.key === 'string' && typeof field.label === 'string')
            .map((field: any) => ({
              key: String(field.key),
              label: String(field.label),
              control: field.control === 'radio'
                ? 'radio'
                : field.control === 'multiselect'
                  ? 'multiselect'
                  : field.control === 'text'
                    ? 'text'
                    : field.control === 'textarea'
                      ? 'textarea'
                      : 'select',
              options: normalizeOptions(field.options),
              optionsSource: typeof field.optionsSource === 'string' ? field.optionsSource : undefined,
              required: Boolean(field.required),
              enabledWhen: normalizeQuestionnaireSectionConditions(field.enabledWhen),
              requiredWhen: normalizeQuestionnaireSectionConditions(field.requiredWhen),
              clearWhenDisabled: field.clearWhenDisabled !== false,
              placeholder: typeof field.placeholder === 'string' ? field.placeholder : undefined,
            }))
          : [],
      }))
    : [];
}

function normalizeQuestionnaireCategories(raw: any): CategoryConfig[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  const normalized: CategoryConfig[] = [];
  const seen = new Set<string>();
  raw
    .filter((item: any) => item && typeof item.key === 'string' && typeof item.label === 'string')
    .forEach((item: any) => {
      const key = normalizeCategoryKey(item.key);
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      normalized.push({
        key,
        label: String(item.label),
        description: typeof item.description === 'string' ? item.description : undefined,
        group: normalizeCategoryGroup(item.group, key),
      });
    });
  return normalized.sort((left, right) => {
    const leftGroupIndex = categoryGroupOrder.indexOf(left.group || 'change');
    const rightGroupIndex = categoryGroupOrder.indexOf(right.group || 'change');
    if (leftGroupIndex !== rightGroupIndex) {
      return leftGroupIndex - rightGroupIndex;
    }
    return left.label.localeCompare(right.label);
  });
}

function normalizeQuestionBank(raw: any): QuestionConfig[] {
  return Array.isArray(raw)
    ? raw
      .filter((item: any) => Number.isFinite(Number(item.id)) && typeof item.text === 'string' && typeof item.category === 'string')
      .map((item: any) => {
        const control: QuestionControl = item.control === 'select'
          ? 'select'
          : item.control === 'multiselect'
            ? 'multiselect'
            : item.control === 'text'
              ? 'text'
              : item.control === 'textarea'
                ? 'textarea'
                : 'radio';

        return {
          id: Number(item.id),
          questionKey: typeof item.questionKey === 'string' ? item.questionKey : undefined,
          text: String(item.text),
          category: normalizeCategoryKey(item.category),
          designIntent: typeof item.designIntent === 'string' ? item.designIntent : undefined,
          control,
          options: normalizeOptions(item.options),
          optionsSource: typeof item.optionsSource === 'string' ? item.optionsSource : undefined,
          placeholder: typeof item.placeholder === 'string' ? item.placeholder : undefined,
          sourceScope: item.sourceScope === 'questionnaire_section' || item.sourceScope === 'assessment_matrix'
            ? item.sourceScope
            : 'question_bank',
          sourceRef: typeof item.sourceRef === 'string' ? item.sourceRef : undefined,
        };
      })
      .sort((left, right) => left.id - right.id)
    : [];
}

export function mergeQuestionnaireConfig(raw: any): QuestionnaireConfig {
  if (!raw || typeof raw !== 'object') {
    return emptyQuestionnaireConfig;
  }

  const rawProjectTypeGuide = raw.projectTypeGuide && typeof raw.projectTypeGuide === 'object' ? raw.projectTypeGuide : {};
  const optionSets = normalizeOptionSets(raw.optionSets);

  return {
    questionnaireSections: normalizeQuestionnaireSections(raw.questionnaireSections),
    questionnaireCategories: Array.isArray(raw.questionnaireCategories)
      ? normalizeQuestionnaireCategories(raw.questionnaireCategories)
      : emptyQuestionnaireConfig.questionnaireCategories,
    questionBank: Array.isArray(raw.questionBank)
      ? normalizeQuestionBank(raw.questionBank)
      : emptyQuestionnaireConfig.questionBank,
    answerTypes: Array.isArray(raw.answerTypes)
      ? normalizeAnswerTypes(raw.answerTypes)
      : emptyQuestionnaireConfig.answerTypes,
    optionSets,
    projectTypeOptions: Array.isArray(raw.projectTypeOptions)
      ? raw.projectTypeOptions
      : emptyQuestionnaireConfig.projectTypeOptions,
    projectTypeGuide: {
      title: typeof rawProjectTypeGuide.title === 'string' ? rawProjectTypeGuide.title : emptyProjectTypeGuide.title,
      introduction: toStringArray(rawProjectTypeGuide.introduction),
      objectives: normalizeGuideItems(rawProjectTypeGuide.objectives),
      scopeIntro: typeof rawProjectTypeGuide.scopeIntro === 'string' ? rawProjectTypeGuide.scopeIntro : emptyProjectTypeGuide.scopeIntro,
      scopeProjectTypes: toStringArray(rawProjectTypeGuide.scopeProjectTypes),
      scopeNote: typeof rawProjectTypeGuide.scopeNote === 'string' ? rawProjectTypeGuide.scopeNote : emptyProjectTypeGuide.scopeNote,
      corePrinciples: normalizeGuideItems(rawProjectTypeGuide.corePrinciples),
      governanceBoundary: toStringArray(rawProjectTypeGuide.governanceBoundary),
      recommendedUsage: toStringArray(rawProjectTypeGuide.recommendedUsage),
      artifactSelectionIntro: toStringArray(rawProjectTypeGuide.artifactSelectionIntro),
      legend: normalizeGuideLegend(rawProjectTypeGuide.legend),
      note: typeof rawProjectTypeGuide.note === 'string' ? rawProjectTypeGuide.note : emptyProjectTypeGuide.note,
    },
    assessmentMatrices: normalizeAssessmentMatrices(raw.assessmentMatrices),
    projectTypeProfiles: normalizeProjectTypeProfiles(raw.projectTypeProfiles),
    applicationCountRangeOptions: Array.isArray(raw.applicationCountRangeOptions)
      ? normalizeOptions(raw.applicationCountRangeOptions)
      : emptyQuestionnaireConfig.applicationCountRangeOptions,
    externalSystemCountRangeOptions: Array.isArray(raw.externalSystemCountRangeOptions)
      ? normalizeOptions(raw.externalSystemCountRangeOptions)
      : emptyQuestionnaireConfig.externalSystemCountRangeOptions,
    newApplicationCountRangeOptions: Array.isArray(raw.newApplicationCountRangeOptions)
      ? normalizeOptions(raw.newApplicationCountRangeOptions)
      : emptyQuestionnaireConfig.newApplicationCountRangeOptions,
    modifiedApplicationCountRangeOptions: Array.isArray(raw.modifiedApplicationCountRangeOptions)
      ? normalizeOptions(raw.modifiedApplicationCountRangeOptions)
      : emptyQuestionnaireConfig.modifiedApplicationCountRangeOptions,
    dataCenterCountRangeOptions: Array.isArray(raw.dataCenterCountRangeOptions)
      ? normalizeOptions(raw.dataCenterCountRangeOptions)
      : emptyQuestionnaireConfig.dataCenterCountRangeOptions,
    cloudRegionScopeOptions: Array.isArray(raw.cloudRegionScopeOptions)
      ? normalizeOptions(raw.cloudRegionScopeOptions)
      : emptyQuestionnaireConfig.cloudRegionScopeOptions,
    techStackKindsCountRangeOptions: Array.isArray(raw.techStackKindsCountRangeOptions)
      ? normalizeOptions(raw.techStackKindsCountRangeOptions)
      : emptyQuestionnaireConfig.techStackKindsCountRangeOptions,
    integrationTechKindsCountRangeOptions: Array.isArray(raw.integrationTechKindsCountRangeOptions)
      ? normalizeOptions(raw.integrationTechKindsCountRangeOptions)
      : emptyQuestionnaireConfig.integrationTechKindsCountRangeOptions,
  };
}

function normalizeConcernScores(raw: any, fallbackScore = 8): ConcernScoreMapping[] {
  if (Array.isArray(raw?.concernScores)) {
    const seen = new Set<string>();
    return raw.concernScores
      .filter((item: any) => {
        const concernKey = String(item?.concernKey || '').trim();
        if (!concernKey || seen.has(concernKey)) {
          return false;
        }
        seen.add(concernKey);
        return true;
      })
      .map((item: any) => ({
        concernKey: String(item.concernKey),
        score: Number.isFinite(Number(item.score)) ? Number(item.score) : fallbackScore,
        severity: Number.isFinite(Number(item.severity)) ? Number(item.severity) : undefined,
        likelihood: Number.isFinite(Number(item.likelihood)) ? Number(item.likelihood) : undefined,
        note: item.note ? String(item.note) : undefined,
      }));
  }
  if (Array.isArray(raw?.concernKeys)) {
    const score = Number.isFinite(Number(raw.score)) ? Number(raw.score) : fallbackScore;
    return toConcernScores(raw.concernKeys.map(String), score);
  }
  return [];
}

export function mergeConcernMappingConfig(raw: any): ConcernMappingConfig {
  if (!raw || typeof raw !== 'object') {
    return emptyConcernMappingConfig;
  }

  const legacyQuestionMappings = Array.isArray(raw.questionBank)
    ? raw.questionBank
      .filter((item: any) => Array.isArray(item.mappedConcernKeys) && item.mappedConcernKeys.length > 0)
      .map((item: any) => ({
        questionId: Number(item.id),
        answer: 'Y',
        concernScores: toConcernScores(item.mappedConcernKeys.map(String), Number(item.score) || 8),
        hints: Array.isArray(item.mappedConcernHints) ? item.mappedConcernHints.map(String) : undefined,
      }))
    : [];

  const rawQuestionMappings = Array.isArray(raw.questionConcernMappings)
    ? raw.questionConcernMappings
      .filter((item: any) => Number.isFinite(Number(item.questionId)) && item.answer)
      .map((item: any) => ({
        questionId: Number(item.questionId),
        answer: String(item.answer),
        concernScores: normalizeConcernScores(item),
        hints: Array.isArray(item.hints) ? item.hints.map(String) : undefined,
      }))
    : [];

  const rawRules = Array.isArray(raw.concernActivationRules)
    ? raw.concernActivationRules.map((rule: any) => ({
      ...rule,
      concernScores: normalizeConcernScores(rule, Number(rule.score) || 8),
    }))
    : [];

  return {
    questionConcernMappings: rawQuestionMappings.length > 0
      ? rawQuestionMappings
      : legacyQuestionMappings.length > 0
        ? legacyQuestionMappings
        : emptyConcernMappingConfig.questionConcernMappings,
    concernActivationRules: rawRules.length > 0
      ? rawRules
      : emptyConcernMappingConfig.concernActivationRules,
  };
}
