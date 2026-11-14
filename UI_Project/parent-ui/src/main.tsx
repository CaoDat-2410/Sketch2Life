import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';
import './wow.css';
import './wonder.css';
import './auth.css';
import './scene.css';
import './coverage.css';
import './leaderReview.css';
import './rev5.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
