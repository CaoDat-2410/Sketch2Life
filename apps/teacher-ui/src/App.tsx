import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { TeacherProvider } from "./context/TeacherContext";
import { TeacherLayout } from "./components/TeacherLayout";
import {
  T01LessonWorkspacePage,
  T02LessonAuthoringPage,
  T03DocumentImportReviewPage,
  T04SessionSketchDeckPage,
  T05ClassesAndChildrenPage,
  T06SampleStoryRunPage,
  T07VideoPresentationConfirmationPage,
} from "./pages/TeacherScreens";

export function App() {
  return (
    <BrowserRouter>
      <TeacherProvider>
        <TeacherLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/t01-lesson-workspace" replace />} />
            <Route path="/t01-lesson-workspace" element={<T01LessonWorkspacePage />} />
            <Route path="/t02-lesson-authoring" element={<T02LessonAuthoringPage />} />
            <Route path="/t03-document-import-review" element={<T03DocumentImportReviewPage />} />
            <Route path="/t04-session-sketch-deck" element={<T04SessionSketchDeckPage />} />
            <Route path="/t05-classes-and-children" element={<T05ClassesAndChildrenPage />} />
            <Route path="/t06-sample-story-run" element={<T06SampleStoryRunPage />} />
            <Route path="/t07-video-presentation-confirmation" element={<T07VideoPresentationConfirmationPage />} />
          </Routes>
        </TeacherLayout>
      </TeacherProvider>
    </BrowserRouter>
  );
}

export default App;
