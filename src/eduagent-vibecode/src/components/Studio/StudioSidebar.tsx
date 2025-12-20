import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { 
  Mic, 
  Video, 
  FileText, 
  MoreHorizontal, 
  Play, 
  Download,
  Maximize2,
  Minimize2,
  Edit3,
  Lightbulb,
  Brain,
  Target,
  Calendar
} from "lucide-react";

interface StudioItem {
  id: string;
  title: string;
  type: "audio" | "video" | "mindmap" | "flashcards" | "quiz" | "notes";
  duration?: string;
  timestamp: string;
  status: "completed" | "generating" | "draft";
}

interface StudioSidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const StudioSidebar = ({ isCollapsed, onToggleCollapse }: StudioSidebarProps) => {
  const [items, setItems] = useState<StudioItem[]>([
    {
      id: "1",
      title: "Types and Principles of Workplace Organization",
      type: "notes",
      timestamp: "13 h ago",
      status: "completed"
    },
    {
      id: "2", 
      title: "Operations Management Cards",
      type: "flashcards",
      timestamp: "13 h ago", 
      status: "completed"
    },
    {
      id: "3",
      title: "Points of Decomposition in Production Chain",
      type: "notes",
      timestamp: "13 h ago",
      status: "completed"
    },
    {
      id: "4",
      title: "Operations Introduction",
      type: "audio",
      duration: "8:32",
      timestamp: "1 d ago",
      status: "completed"
    },
    {
      id: "5",
      title: "Operations Introduction",
      type: "notes",
      timestamp: "3 sources • 1 d ago",
      status: "completed"
    }
  ]);

  const getItemIcon = (type: StudioItem["type"], status: StudioItem["status"]) => {
    if (status === "generating") {
      return <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />;
    }
    
    switch (type) {
      case "audio":
        return <Mic className="w-4 h-4 text-primary" />;
      case "video":
        return <Video className="w-4 h-4 text-accent" />;
      case "mindmap":
        return <Brain className="w-4 h-4 text-success" />;
      case "flashcards":
        return <Lightbulb className="w-4 h-4 text-warning" />;
      case "notes":
        return <FileText className="w-4 h-4 text-muted-foreground" />;
      default:
        return <FileText className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: StudioItem["status"]) => {
    switch (status) {
      case "completed":
        return "bg-success/10 text-success border-success/20";
      case "generating":
        return "bg-primary/10 text-primary border-primary/20";
      case "draft":
        return "bg-warning/10 text-warning border-warning/20";
      default:
        return "bg-muted/10 text-muted-foreground border-muted/20";
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-12 bg-card border-l border-border flex flex-col items-center py-4 gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="w-8 h-8 p-0"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
        <div className="flex flex-col gap-2">
          {items.slice(0, 3).map((item) => (
            <div key={item.id} className="w-8 h-8 rounded bg-muted flex items-center justify-center">
              {getItemIcon(item.type, item.status)}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-card border-l border-border flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading font-semibold text-foreground">Studium</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="w-8 h-8 p-0"
          >
            <Minimize2 className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="grid grid-cols-2 gap-2 mb-4">
          <Button variant="outline" size="sm" className="gap-2">
            <Lightbulb className="w-4 h-4" />
            Kartičky
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Target className="w-4 h-4" />
            Kvíz
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-4">
          <Button variant="outline" size="sm" className="gap-2">
            <Brain className="w-4 h-4" />
            Mapa
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Calendar className="w-4 h-4" />
            Plán
          </Button>
        </div>

        <Button variant="outline" size="sm" className="w-full gap-2 mb-4">
          <Mic className="w-4 h-4" />
          Audio přehled
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {items.map((item) => (
            <Card key={item.id} className="p-3 hover:bg-hover transition-colors group cursor-pointer">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {getItemIcon(item.type, item.status)}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-foreground leading-tight mb-1 line-clamp-2">
                      {item.title}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{item.timestamp}</span>
                      {item.duration && (
                        <>
                          <span>•</span>
                          <span>{item.duration}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {item.type === "audio" && (
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                      <Play className="w-3 h-3" />
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                    <Edit3 className="w-3 h-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                    <MoreHorizontal className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};