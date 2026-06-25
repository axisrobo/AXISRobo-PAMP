export interface AppRef {
  readonly id: string;
  readonly name: string;
  readonly status: string;
  readonly geo: string;
  readonly portfolioMgt: string;
}

export interface CapNode {
  readonly id: string;
  readonly name: string;
  readonly nameCn: string;
  readonly level: 1 | 2 | 3;
  readonly parentId: string | null;
  readonly domain: string;
  readonly description: string;
  readonly appCount: number;
  readonly applications: ReadonlyArray<AppRef>;
}

export interface Application {
  readonly appId: string;
  readonly appName: string;
  readonly appFullName: string;
  readonly appOwnership: string;
  readonly appSolutionOwner: string;
  readonly appItOwner: string;
  readonly ownedBy: string;
  readonly appOwnerTower: string;
  readonly appOwnerDomain: string;
  readonly appDtOwner: string;
  readonly appDescription: string;
  readonly portfolioMgt: string;
  readonly appSolutionType: string;
  readonly appClassification: string;
  readonly appStatus: string;
  readonly bizFunction: string;
  readonly geo: string;
  readonly actualK: number | null;
  readonly capabilities: ReadonlyArray<CapRef>;
}

export interface CapRef {
  readonly bcId: string;
  readonly bcName: string;
  readonly lv1Domain: string;
  readonly lv2SubDomain: string;
  readonly lv3CapGroup: string;
}

export interface MappingRow {
  readonly appId: string;
  readonly bcId: string;
}

export interface DataState {
  readonly capabilities: ReadonlyArray<CapNode>;
  readonly applications: ReadonlyArray<Application>;
  readonly mappings: ReadonlyArray<MappingRow>;
  readonly domains: ReadonlyArray<string>;
  readonly dataVersion: string;
  readonly totalL3Count: number;
  readonly versions: ReadonlyArray<string>;
}
