import React, { createContext, useContext, useState, useEffect } from 'react';
import { Platform } from 'react-native';
import type { ScreenId } from '../types';
import type {
  ChildProfile,
  SceneUnderstandingResponse,
  StoryVideoResponse,
  MontessoriActivity,
  FeedbackPayload,
} from '../services/api.types';
import { ApiService } from '../services/api';
import {
  MOCK_CHILDREN,
  MOCK_SCENE_UNDERSTANDING,
  MOCK_STORY_VIDEO,
  MOCK_ACTIVITIES,
} from '../services/mockData';

interface AppContextType {
  // Navigation
  currentScreen: ScreenId;
  navigate: (screen: ScreenId) => void;
  goBack: () => void;
  resetTo: (screen: ScreenId) => void;
  canGoBack: boolean;

  // Child Profile
  childrenList: ChildProfile[];
  selectedChild: ChildProfile;
  setSelectedChild: (child: ChildProfile) => void;
  selectedAgeGroup: string;
  setSelectedAgeGroup: (ageGroup: string) => void;

  // Drawing
  drawingImage: string;
  setDrawingImage: (img: string) => void;

  // Voice
  isRecording: boolean;
  voiceDuration: number;
  toggleRecording: () => void;
  setVoiceDuration: (dur: number) => void;
  voiceTranscript: string;

  // AI Pipeline
  aiProgress: number;
  sceneData: SceneUnderstandingResponse;
  storyData: StoryVideoResponse;
  runAiSimulation: () => void;

  // Montessori Activity
  activitiesList: MontessoriActivity[];
  selectedActivity: MontessoriActivity;
  setSelectedActivity: (activity: MontessoriActivity) => void;
  materialsChecklist: Record<string, boolean>;
  toggleMaterialCheck: (id: string) => void;
  stepsChecklist: Record<number, boolean>;
  toggleStepCheck: (stepNumber: number) => void;

  // Feedback Loop
  completionStatus: 'completed' | 'partial' | 'not_attempted';
  setCompletionStatus: (status: 'completed' | 'partial' | 'not_attempted') => void;
  interestScore: number;
  setInterestScore: (score: number) => void;
  independenceScore: number;
  setIndependenceScore: (score: number) => void;
  selectedObservationTags: string[];
  toggleObservationTag: (tag: string) => void;
  parentNotes: string;
  setParentNotes: (notes: string) => void;
  isSavingFeedback: boolean;
  saveFeedback: () => Promise<boolean>;
  toastMessage: string | null;
  clearToast: () => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Navigation Stack
  const getInitialScreen = (): ScreenId => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const s = params.get('screen') as ScreenId;
      if (s) return s;
    }
    return 'splash';
  };

  const [currentScreen, setCurrentScreen] = useState<ScreenId>(getInitialScreen);
  const [history, setHistory] = useState<ScreenId[]>([getInitialScreen()]);

  const navigate = (screen: ScreenId) => {
    setCurrentScreen(screen);
    setHistory((prev) => [...prev, screen]);
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
      const url = new URL(window.location.href);
      url.searchParams.set('screen', screen);
      window.history.replaceState({}, '', url.toString());
    }
  };

  const goBack = () => {
    if (history.length > 1) {
      const newHistory = [...history];
      newHistory.pop(); // Remove current
      const prevScreen = newHistory[newHistory.length - 1];
      setHistory(newHistory);
      setCurrentScreen(prevScreen);
      if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
        const url = new URL(window.location.href);
        url.searchParams.set('screen', prevScreen);
        window.history.replaceState({}, '', url.toString());
      }
    } else {
      navigate('dashboard');
    }
  };

  const resetTo = (screen: ScreenId) => {
    setHistory([screen]);
    setCurrentScreen(screen);
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.history) {
      const url = new URL(window.location.href);
      url.searchParams.set('screen', screen);
      window.history.replaceState({}, '', url.toString());
    }
  };

  // Child Profile
  const [childrenList] = useState<ChildProfile[]>(MOCK_CHILDREN);
  const [selectedChild, setSelectedChild] = useState<ChildProfile>(MOCK_CHILDREN[0]);
  const [selectedAgeGroup, setSelectedAgeGroup] = useState<string>('5-6');

  // Drawing
  const [drawingImage, setDrawingImage] = useState<string>('cat-drawing-sample');

  // Voice
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [voiceDuration, setVoiceDuration] = useState<number>(12);
  const voiceTranscript =
    'Chú bướm bay đến bông hoa, ở một khu vườn đầy nắng. Chúng mình cùng chơi và khám phá thế giới xung quanh nhé!';

  const toggleRecording = () => {
    setIsRecording((prev) => !prev);
  };

  // AI Pipeline
  const [aiProgress, setAiProgress] = useState<number>(70);
  const [sceneData] = useState<SceneUnderstandingResponse>(MOCK_SCENE_UNDERSTANDING);
  const [storyData] = useState<StoryVideoResponse>(MOCK_STORY_VIDEO);

  const runAiSimulation = () => {
    setAiProgress(20);
    const t1 = setTimeout(() => setAiProgress(45), 600);
    const t2 = setTimeout(() => setAiProgress(75), 1400);
    const t3 = setTimeout(() => {
      setAiProgress(100);
      setTimeout(() => navigate('scene_understanding'), 600);
    }, 2200);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  };

  // Montessori Activities
  const [activitiesList] = useState<MontessoriActivity[]>(MOCK_ACTIVITIES);
  const [selectedActivity, setSelectedActivity] = useState<MontessoriActivity>(MOCK_ACTIVITIES[0]);

  // Checklists
  const [materialsChecklist, setMaterialsChecklist] = useState<Record<string, boolean>>({
    m1: true,
    m2: true,
    m3: true,
    m4: true,
  });

  const toggleMaterialCheck = (id: string) => {
    setMaterialsChecklist((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const [stepsChecklist, setStepsChecklist] = useState<Record<number, boolean>>({
    1: true,
    2: true,
    3: false,
    4: false,
  });

  const toggleStepCheck = (stepNumber: number) => {
    setStepsChecklist((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  // Feedback State
  const [completionStatus, setCompletionStatus] = useState<'completed' | 'partial' | 'not_attempted'>(
    'completed'
  );
  const [interestScore, setInterestScore] = useState<number>(5);
  const [independenceScore, setIndependenceScore] = useState<number>(4);
  const [selectedObservationTags, setSelectedObservationTags] = useState<string[]>([
    'Nhớ vòi bướm hút mật',
    'Tự tay dán cánh',
  ]);
  const [parentNotes, setParentNotes] = useState<string>(
    'Bé An rất vui khi cầm chú bướm giấy tự làm đi quanh nhà vờ như bướm bay hút mật hoa!'
  );
  const [isSavingFeedback, setIsSavingFeedback] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const toggleObservationTag = (tag: string) => {
    setSelectedObservationTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const clearToast = () => setToastMessage(null);

  const saveFeedback = async (): Promise<boolean> => {
    setIsSavingFeedback(true);
    try {
      const payload: FeedbackPayload = {
        activityId: selectedActivity.id,
        childId: selectedChild.id,
        completionStatus,
        interestScore,
        independenceScore,
        selectedObservationTags,
        parentNotes,
      };

      const result = await ApiService.submitFeedback(payload);
      setIsSavingFeedback(false);
      if (result.success) {
        setToastMessage(`✨ Đã lưu nhật ký cho bé ${selectedChild.name}!`);
        setTimeout(() => {
          setToastMessage(null);
          resetTo('dashboard');
        }, 1500);
        return true;
      }
      return false;
    } catch {
      setIsSavingFeedback(false);
      setToastMessage('Có lỗi xảy ra khi lưu. Đã lưu tạm vào máy!');
      setTimeout(() => {
        setToastMessage(null);
        resetTo('dashboard');
      }, 1500);
      return false;
    }
  };

  return (
    <AppContext.Provider
      value={{
        currentScreen,
        navigate,
        goBack,
        resetTo,
        canGoBack: history.length > 1,

        childrenList,
        selectedChild,
        setSelectedChild,
        selectedAgeGroup,
        setSelectedAgeGroup,

        drawingImage,
        setDrawingImage,

        isRecording,
        voiceDuration,
        toggleRecording,
        setVoiceDuration,
        voiceTranscript,

        aiProgress,
        sceneData,
        storyData,
        runAiSimulation,

        activitiesList,
        selectedActivity,
        setSelectedActivity,
        materialsChecklist,
        toggleMaterialCheck,
        stepsChecklist,
        toggleStepCheck,

        completionStatus,
        setCompletionStatus,
        interestScore,
        setInterestScore,
        independenceScore,
        setIndependenceScore,
        selectedObservationTags,
        toggleObservationTag,
        parentNotes,
        setParentNotes,
        isSavingFeedback,
        saveFeedback,
        toastMessage,
        clearToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
