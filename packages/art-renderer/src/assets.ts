import type {ArtAnimationPlan, ArtObject, ChildArtAsset} from './contracts';

export interface LoadedChildArtAsset {
  readonly objectId: string;
  readonly sourceAssetId: string;
  readonly sourceAssetVersion: string;
  readonly cropVersion?: string;
  readonly maskVersion?: string;
  readonly sourceSha256?: string;
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
