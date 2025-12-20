import { useState } from "react";
import { Header } from "@/components/Layout/Header";
import { SourcesSidebar } from "@/components/Sources/SourcesSidebar";
import { MainView } from "@/components/EduAgent/MainView";
import { StudioSidebar } from "@/components/Studio/StudioSidebar";

export const NotebookLM = () => {
  const [sourcesCollapsed, setSourcesCollapsed] = useState(false);
  const [studioCollapsed, setStudioCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header 
        projectTitle="EduAgent - Principy managementu" 
        isPublic={true}
      />
      
      <div className="flex-1 flex overflow-hidden min-h-0">
        <SourcesSidebar 
          isCollapsed={sourcesCollapsed}
          onToggleCollapse={() => setSourcesCollapsed(!sourcesCollapsed)}
        />
        
        <MainView />
        
        <StudioSidebar
          isCollapsed={studioCollapsed}
          onToggleCollapse={() => setStudioCollapsed(!studioCollapsed)}
        />
      </div>
    </div>
  );
};