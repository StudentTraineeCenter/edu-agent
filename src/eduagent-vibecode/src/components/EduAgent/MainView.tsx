import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChatArea } from "@/components/Chat/ChatArea";
import { FlashcardsGenerator } from "./FlashcardsGenerator";
import { QuizGenerator } from "./QuizGenerator";
import { StudyPlan } from "./StudyPlan";
import { MindMap } from "./MindMap";
import { 
  MessageSquare, 
  Brain, 
  Target, 
  Calendar, 
  Lightbulb,
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle
} from "lucide-react";

export const MainView = () => {
  const [activeTab, setActiveTab] = useState("chat");

  const getTabIcon = (tab: string) => {
    switch (tab) {
      case "chat": return <MessageSquare className="w-4 h-4" />;
      case "flashcards": return <Lightbulb className="w-4 h-4" />;
      case "quiz": return <Target className="w-4 h-4" />;
      case "mindmap": return <Brain className="w-4 h-4" />;
      case "study-plan": return <Calendar className="w-4 h-4" />;
      default: return null;
    }
  };

  // Mock quick stats for the dashboard
  const quickStats = {
    studyStreak: 5,
    completedTasks: 8,
    totalTasks: 12,
    avgScore: 78,
    studyTime: 180 // minutes this week
  };

  return (
    <div className="flex-1 flex flex-col bg-background min-w-0 overflow-hidden">
      {/* Quick Stats Bar */}
      <div className="p-4 border-b border-border bg-card/50">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-success" />
            <span className="text-muted-foreground">Úkoly:</span>
            <span className="font-medium text-foreground">{quickStats.completedTasks}/{quickStats.totalTasks}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <span className="text-muted-foreground">Průměr:</span>
            <span className="font-medium text-foreground">{quickStats.avgScore}%</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-warning" />
            <span className="text-muted-foreground">Týden:</span>
            <span className="font-medium text-foreground">{Math.floor(quickStats.studyTime / 60)}h {quickStats.studyTime % 60}m</span>
          </div>
          
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-destructive" />
            <span className="text-muted-foreground">Série:</span>
            <span className="font-medium text-foreground">{quickStats.studyStreak} dní</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <div className="border-b border-border bg-card">
          <TabsList className="h-auto p-1 bg-transparent w-full justify-start rounded-none">
            <TabsTrigger 
              value="chat" 
              className="gap-2 data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
            >
              {getTabIcon("chat")}
              Chat
            </TabsTrigger>
            <TabsTrigger 
              value="flashcards"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
            >
              {getTabIcon("flashcards")}
              Kartičky
            </TabsTrigger>
            <TabsTrigger 
              value="quiz"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
            >
              {getTabIcon("quiz")}
              Kvíz
            </TabsTrigger>
            <TabsTrigger 
              value="mindmap"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
            >
              {getTabIcon("mindmap")}
              Mapa
            </TabsTrigger>
            <TabsTrigger 
              value="study-plan"
              className="gap-2 data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none"
            >
              {getTabIcon("study-plan")}
              Studijní plán
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-hidden">
          <TabsContent value="chat" className="h-full m-0">
            <ChatArea />
          </TabsContent>
          
          <TabsContent value="flashcards" className="h-full m-0 overflow-auto">
            <FlashcardsGenerator />
          </TabsContent>
          
          <TabsContent value="quiz" className="h-full m-0 overflow-auto">
            <QuizGenerator />
          </TabsContent>
          
          <TabsContent value="mindmap" className="h-full m-0 overflow-auto">
            <MindMap />
          </TabsContent>
          
          <TabsContent value="study-plan" className="h-full m-0 overflow-auto">
            <StudyPlan />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};