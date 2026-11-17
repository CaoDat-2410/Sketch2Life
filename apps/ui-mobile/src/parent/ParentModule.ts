import { ParentAccountUseCases } from './application/use-cases/ParentAccountUseCases';
import { ParentLearningUseCases } from './application/use-cases/ParentLearningUseCases';
import { ParentLessonUseCases } from './application/use-cases/ParentLessonUseCases';
import { ParentProfileUseCases } from './application/use-cases/ParentProfileUseCases';
import { ParentPlatformUseCases } from './application/use-cases/ParentPlatformUseCases';
import { ParentAuth } from './infrastructure/auth/ParentAuth';
import { parentConfig } from './infrastructure/config';
import { ParentApi } from './infrastructure/http/ParentApi';
import type { ParentApplicationModule } from './application/ports/ParentApplicationModule';

const identity = new ParentAuth();
const api = new ParentApi(identity);

export const parentModule: ParentApplicationModule = Object.freeze({
  publicSettings: Object.freeze({
    googleAndroidClientId: parentConfig.googleAndroidClientId,
    googleWebClientId: parentConfig.googleWebClientId,
  }),
  account: new ParentAccountUseCases(identity),
  profiles: new ParentProfileUseCases(api),
  lessons: new ParentLessonUseCases(api),
  learning: new ParentLearningUseCases(api),
  platform: new ParentPlatformUseCases(api),
});
