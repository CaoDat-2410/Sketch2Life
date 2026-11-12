import React from 'react';
import { createRoot } from 'react-dom/client';
import { UnifiedWebApp } from '../../shared/UnifiedWebApp';
import '../../shared/webWorkspace.css';
import '../../shared/roleDashboards.css';
import '../../shared/unifiedWeb.css';
import '../../shared/roleFlows.css';
import '../../shared/visualPolish.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><UnifiedWebApp/></React.StrictMode>);
