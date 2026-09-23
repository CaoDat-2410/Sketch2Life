import type {ArtAnimationPlan, ArtObject, ChildArtAsset, SourceRegion} from './contracts';

export interface LoadedChildArtAsset {
  readonly objectId: string;
  readonly sourceAssetId: string;
  readonly sourceAssetVersion: string;
  readonly cropVersion?: string;
  readonly maskVersion?: string;
  readonly sourceSha256?: string;
  readonly sourceRegion?: SourceRegion;
  readonly uri: string;
  readonly extractionStatus: ArtObject['extractionStatus'];
}

function toLoadedAsset(object: ArtObject): LoadedChildArtAsset {
  const asset: ChildArtAsset = object.asset;
  return {
    objectId: object.id,
    sourceAssetId: asset.sourceAssetId,
    sourceAssetVersion: asset.sourceAssetVersion,
    cropVersion: asset.cropVersion,
    maskVersion: asset.maskVersion,
    sourceSha256: asset.sourceSha256,
    sourceRegion: asset.sourceRegion,
    uri: asset.uri,
    extractionStatus: object.extractionStatus,
  };
}

/**
 * Resolve render instructions without modifying source assets. Browser-specific
 * texture loading happens later, after this provenance boundary is established.
 */
export function loadChildArtAssetInstructions(plan: ArtAnimationPlan): readonly LoadedChildArtAsset[] {
  return plan.objects.map(toLoadedAsset);
}
