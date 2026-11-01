import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ParentProvider } from "./context/ParentContext";
import { MobileLayout } from "./components/MobileLayout";
import {
  P01LessonLibraryPage,
  P02LessonDetailPage,
  P03DrawingLineGuidePage,
  P04CaptureSubjectConfirmationPage,
  P05ContextIdeaConfirmationPage,
  P06StoryReviewPage,
  P07VideoJobStatusPage,
  P08VideoAndActivitiesPage,
  P09HistoryFeedbackPage,
  P10ChildProfilesPage,
  P11AuthenticationPage,
  P12VideoQuotaPage,
} from "./pages/ParentScreens";

export function App() {
  return (
    <BrowserRouter>
      <ParentProvider>
        <MobileLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/p01-lesson-library" replace />} />
            <Route path="/p01-lesson-library" element={<P01LessonLibraryPage />} />
            <Route path="/p02-lesson-detail" element={<P02LessonDetailPage />} />
            <Route path="/p03-drawing-line-guide" element={<P03DrawingLineGuidePage />} />
            <Route path="/p04-capture-subject-confirmation" element={<P04CaptureSubjectConfirmationPage />} />
            <Route path="/p05-context-idea-confirmation" element={<P05ContextIdeaConfirmationPage />} />
            <Route path="/p06-story-review" element={<P06StoryReviewPage />} />
            <Route path="/p07-video-job-status" element={<P07VideoJobStatusPage />} />
            <Route path="/p08-video-and-activities" element={<P08VideoAndActivitiesPage />} />
            <Route path="/p09-history-feedback" element={<P09HistoryFeedbackPage />} />
            <Route path="/p10-child-profiles" element={<P10ChildProfilesPage />} />
            <Route path="/p11-authentication" element={<P11AuthenticationPage />} />
            <Route path="/p12-video-quota" element={<P12VideoQuotaPage />} />
          </Routes>
        </MobileLayout>
      </ParentProvider>
    </BrowserRouter>
  );
}

export default App;
