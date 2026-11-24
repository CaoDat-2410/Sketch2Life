import { Ionicons } from '@expo/vector-icons';
import type { ImageSourcePropType } from 'react-native';

export type TopicVisual = Readonly<{
  image?: ImageSourcePropType;
  color: string;
  icon: keyof typeof Ionicons.glyphMap;
}>;

const TOPIC_VISUALS: Readonly<Record<string, TopicVisual>> = {
  animals: { image: require('../../../../assets/topics/topic-animals-landscape.png'), color: '#80C7F5', icon: 'paw-outline' },
  nature: { image: require('../../../../assets/topics/topic-nature-landscape.png'), color: '#82C7F5', icon: 'leaf-outline' },
  transport: { image: require('../../../../assets/topics/topic-transport.png'), color: '#B9E0FF', icon: 'car-outline' },
  ocean: { image: require('../../../../assets/topics/topic-ocean.png'), color: '#B7EAF7', icon: 'fish-outline' },
  space: { image: require('../../../../assets/topics/topic-space-landscape.png'), color: '#30206F', icon: 'planet-outline' },
  'fairy-tale': { image: require('../../../../assets/topics/topic-fairy-tale.png'), color: '#F6D9F2', icon: 'sparkles-outline' },
  home: { color: '#F8E2C8', icon: 'home-outline' },
  food: { color: '#FFE2B8', icon: 'nutrition-outline' },
  kitchen: { color: '#FFE8D3', icon: 'restaurant-outline' },
  school: { color: '#DCEBFF', icon: 'school-outline' },
  neighborhood: { color: '#E9E0FF', icon: 'business-outline' },
  clothing: { color: '#FFE0EA', icon: 'shirt-outline' },
  toys: { color: '#FFF0B8', icon: 'game-controller-outline' },
  farm: { color: '#DDF3D7', icon: 'leaf-outline' },
  birds: { color: '#D9F1F5', icon: 'egg-outline' },
  insects: { color: '#E5F2C8', icon: 'bug-outline' },
  weather: { color: '#DCEBFA', icon: 'cloud-outline' },
  music: { color: '#F0DFFF', icon: 'musical-notes-outline' },
};

const SUBJECT_ICONS: Readonly<Record<string, keyof typeof Ionicons.glyphMap>> = {
  cat: 'paw-outline', dog: 'paw-outline', rabbit: 'paw-outline', turtle: 'paw-outline',
  horse: 'paw-outline', elephant: 'paw-outline', deer: 'paw-outline', bear: 'paw-outline',
  fish: 'fish-outline', whale: 'fish-outline', dolphin: 'fish-outline', octopus: 'fish-outline',
  crab: 'fish-outline', seahorse: 'fish-outline', starfish: 'fish-outline', shell: 'fish-outline',
  butterfly: 'bug-outline', snail: 'bug-outline', mushroom: 'leaf-outline', pinecone: 'leaf-outline',
  flower: 'leaf-outline', tree: 'leaf-outline', leaf: 'leaf-outline', plant: 'leaf-outline',
  car: 'car-outline', bicycle: 'bicycle-outline', train: 'train-outline', airplane: 'airplane-outline',
  boat: 'boat-outline', bus: 'bus-outline', scooter: 'bicycle-outline', truck: 'car-outline',
  rocket: 'planet-outline', planet: 'planet-outline', moon: 'moon-outline', star: 'star-outline',
  cloud: 'cloud-outline', rainbow: 'color-palette-outline', sun: 'sunny-outline',
  home: 'home-outline', school: 'school-outline', house: 'home-outline',
  apple: 'nutrition-outline', bread: 'restaurant-outline', cake: 'restaurant-outline',
  drum: 'musical-notes-outline', guitar: 'musical-notes-outline', ball: 'football-outline',
};

const SUBJECT_ART_BACKGROUNDS = ['#F1E7FF', '#DDF3E8', '#FFF0B8'] as const;

export function getTopicVisual(topicId: string): TopicVisual {
  return TOPIC_VISUALS[topicId] ?? { color: '#E9E0FF', icon: 'sparkles-outline' };
}

export function getDrawingSubjectVisual(subjectId: string, topicId: string, index: number): Readonly<{
  icon: keyof typeof Ionicons.glyphMap;
  backgroundColor: string;
}> {
  return {
    icon: SUBJECT_ICONS[subjectId] ?? getTopicVisual(topicId).icon,
    backgroundColor: SUBJECT_ART_BACKGROUNDS[index % SUBJECT_ART_BACKGROUNDS.length],
  };
}
