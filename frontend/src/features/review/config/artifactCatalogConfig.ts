export type ArtifactCatalogItem = {
  key: string;
  name: string;
  purpose: string;
  typicalContents: string[];
  supportedViewpoints: string[];
  isActive: boolean;
  sortOrder: number;
};

export type ArtifactCatalogConfig = {
  catalogName: string;
  stage: string;
  artifactTypes: ArtifactCatalogItem[];
};

export const emptyArtifactCatalogConfig: ArtifactCatalogConfig = {
  catalogName: 'Architecture Artifact Catalog',
  stage: 'Preparation',
  artifactTypes: [],
};

function normalizeStringArray(raw: unknown): string[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
}

function normalizeArtifactItem(raw: unknown, index: number): ArtifactCatalogItem | null {
  if (!raw || typeof raw !== 'object') {
    return null;
  }

  const item = raw as Record<string, unknown>;
  const key = typeof item.key === 'string' ? item.key.trim() : '';
  const name = typeof item.name === 'string' ? item.name.trim() : '';

  if (!key || !name) {
    return null;
  }

  return {
    key,
    name,
    purpose: typeof item.purpose === 'string' ? item.purpose.trim() : '',
    typicalContents: normalizeStringArray(item.typicalContents),
    supportedViewpoints: normalizeStringArray(item.supportedViewpoints),
    isActive: item.isActive !== false,
    sortOrder: Number(item.sortOrder) > 0 ? Number(item.sortOrder) : index + 1,
  };
}

export function mergeArtifactCatalogConfig(raw: unknown): ArtifactCatalogConfig {
  if (!raw || typeof raw !== 'object') {
    return {
      ...emptyArtifactCatalogConfig,
      artifactTypes: [],
    };
  }

  const config = raw as Record<string, unknown>;
  const artifactTypes = Array.isArray(config.artifactTypes)
    ? config.artifactTypes
      .map((item, index) => normalizeArtifactItem(item, index))
      .filter((item): item is ArtifactCatalogItem => Boolean(item))
      .sort((left, right) => left.sortOrder - right.sortOrder || left.name.localeCompare(right.name))
    : [];

  return {
    catalogName: typeof config.catalogName === 'string' && config.catalogName.trim()
      ? config.catalogName.trim()
      : emptyArtifactCatalogConfig.catalogName,
    stage: typeof config.stage === 'string' && config.stage.trim()
      ? config.stage.trim()
      : emptyArtifactCatalogConfig.stage,
    artifactTypes,
  };
}