export type GuideTextItem = {
  id: string;
  title: string;
  description: string;
};

export type ViewpointDefinition = {
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

export type ViewpointArtifactMappingConfig = {
  guideName: string;
  stage: string;
  positioning: string;
  objectives: GuideTextItem[];
  corePrinciples: GuideTextItem[];
  relatedGuides: string[];
  viewpoints: ViewpointDefinition[];
};

export const emptyViewpointArtifactMappingConfig: ViewpointArtifactMappingConfig = {
  guideName: 'Architecture Viewpoint and Artifact Mapping Guide',
  stage: 'Preparation',
  positioning: '',
  objectives: [],
  corePrinciples: [],
  relatedGuides: [],
  viewpoints: [],
};

function normalizeString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => normalizeString(item))
    .filter(Boolean);
}

function normalizeGuideTextItem(raw: unknown): GuideTextItem | null {
  if (!raw || typeof raw !== 'object') {
    return null;
  }

  const item = raw as Record<string, unknown>;
  const title = normalizeString(item.title);
  const description = normalizeString(item.description);

  if (!title || !description) {
    return null;
  }

  return {
    id: normalizeString(item.id) || title,
    title,
    description,
  };
}

function normalizeViewpoint(raw: unknown, index: number): ViewpointDefinition | null {
  if (!raw || typeof raw !== 'object') {
    return null;
  }

  const item = raw as Record<string, unknown>;
  const viewpoint = normalizeString(item.viewpoint);
  if (!viewpoint) {
    return null;
  }

  const mandatoryArtifacts = normalizeStringArray(item.mandatoryArtifacts);
  const optionalArtifacts = normalizeStringArray(item.optionalArtifacts)
    .filter((artifactKey) => !mandatoryArtifacts.includes(artifactKey));

  return {
    number: Number(item.number) > 0 ? Number(item.number) : index + 1,
    layer: normalizeString(item.layer),
    viewpoint,
    concernKeys: normalizeStringArray(item.concernKeys).map((item) => item.toUpperCase()),
    mandatoryArtifacts,
    optionalArtifacts,
    logicalPhysical: normalizeString(item.logicalPhysical) || 'L',
    structureBehavior: normalizeString(item.structureBehavior) || 'S',
    purpose: normalizeString(item.purpose),
    example: normalizeString(item.example),
    primarySource: normalizeString(item.primarySource),
    audience: normalizeString(item.audience),
    notes: normalizeString(item.notes),
    isActive: item.isActive !== false,
    sortOrder: Number(item.sortOrder) > 0 ? Number(item.sortOrder) : index + 1,
  };
}

export function mergeViewpointArtifactMappingConfig(raw: unknown): ViewpointArtifactMappingConfig {
  if (!raw || typeof raw !== 'object') {
    return {
      ...emptyViewpointArtifactMappingConfig,
      objectives: [],
      corePrinciples: [],
      relatedGuides: [],
      viewpoints: [],
    };
  }

  const config = raw as Record<string, unknown>;

  return {
    guideName: normalizeString(config.guideName) || emptyViewpointArtifactMappingConfig.guideName,
    stage: normalizeString(config.stage) || emptyViewpointArtifactMappingConfig.stage,
    positioning: normalizeString(config.positioning),
    objectives: Array.isArray(config.objectives)
      ? config.objectives
        .map((item) => normalizeGuideTextItem(item))
        .filter((item): item is GuideTextItem => Boolean(item))
      : [],
    corePrinciples: Array.isArray(config.corePrinciples)
      ? config.corePrinciples
        .map((item) => normalizeGuideTextItem(item))
        .filter((item): item is GuideTextItem => Boolean(item))
      : [],
    relatedGuides: normalizeStringArray(config.relatedGuides),
    viewpoints: Array.isArray(config.viewpoints)
      ? config.viewpoints
        .map((item, index) => normalizeViewpoint(item, index))
        .filter((item): item is ViewpointDefinition => Boolean(item))
        .sort((left, right) => left.sortOrder - right.sortOrder || left.number - right.number)
      : [],
  };
}