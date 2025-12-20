import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Plus, Search, FileText, BarChart3, Maximize2, Minimize2, MoreHorizontal, Download, Edit, Trash2, Share, Copy } from "lucide-react";

interface Source {
  id: string;
  name: string;
  type: "pdf" | "text" | "audio" | "video";
  size?: string;
  selected: boolean;
}

interface SourcesSidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const SourcesSidebar = ({ isCollapsed, onToggleCollapse }: SourcesSidebarProps) => {
  const [sources, setSources] = useState<Source[]>([
    {
      id: "1",
      name: "Introduction to Operations Management.pdf",
      type: "pdf",
      size: "2.3 MB",
      selected: true,
    },
    {
      id: "2", 
      name: "Operations_Management_2025_Case_Study.pdf",
      type: "pdf",
      size: "1.8 MB",
      selected: true,
    },
    {
      id: "3",
      name: "Operations Management Analysis.mda",
      type: "text",
      size: "892 KB",
      selected: true,
    },
  ]);

  const [selectAll, setSelectAll] = useState(true);

  const handleSelectAll = (checked: boolean) => {
    setSelectAll(checked);
    setSources(sources.map(source => ({ ...source, selected: checked })));
  };

  const handleSelectSource = (id: string, checked: boolean) => {
    setSources(sources.map(source => 
      source.id === id ? { ...source, selected: checked } : source
    ));
    setSelectAll(false);
  };

  const getSourceIcon = (type: Source["type"]) => {
    switch (type) {
      case "pdf":
        return <FileText className="w-4 h-4 text-destructive" />;
      case "text":
        return <BarChart3 className="w-4 h-4 text-primary" />;
      default:
        return <FileText className="w-4 h-4 text-muted-foreground" />;
    }
  };

  if (isCollapsed) {
    return (
      <div className="w-12 bg-card border-r border-border flex flex-col items-center py-4 gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="w-8 h-8 p-0"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
        <div className="flex flex-col gap-2">
          {sources.slice(0, 3).map((source) => (
            <div key={source.id} className="w-8 h-8 rounded bg-muted flex items-center justify-center">
              {getSourceIcon(source.type)}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-card border-r border-border flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading font-semibold text-foreground">Materiály</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="w-8 h-8 p-0"
          >
            <Minimize2 className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex gap-2 mb-4">
          <Button className="gap-2 flex-1" size="sm">
            <Plus className="w-4 h-4" />
            Nahrát
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Search className="w-4 h-4" />
            Hledat
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Checkbox
            id="select-all"
            checked={selectAll}
            onCheckedChange={handleSelectAll}
          />
          <label htmlFor="select-all" className="text-sm text-muted-foreground">
            Vybrat všechny materiály
          </label>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {sources.map((source) => (
            <div
              key={source.id}
              className="group flex items-start gap-3 p-3 rounded-lg hover:bg-hover transition-colors"
            >
              <Checkbox
                checked={source.selected}
                onCheckedChange={(checked) => handleSelectSource(source.id, checked as boolean)}
              />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {getSourceIcon(source.type)}
                  <span className="text-sm font-medium text-foreground truncate">
                    {source.name}
                  </span>
                </div>
                {source.size && (
                  <p className="text-xs text-muted-foreground">{source.size}</p>
                )}
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0"
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-popover border border-border shadow-elevated">
                  <DropdownMenuItem className="gap-2 cursor-pointer">
                    <Download className="w-4 h-4" />
                    Stáhnout
                  </DropdownMenuItem>
                  <DropdownMenuItem className="gap-2 cursor-pointer">
                    <Edit className="w-4 h-4" />
                    Přejmenovat
                  </DropdownMenuItem>
                  <DropdownMenuItem className="gap-2 cursor-pointer">
                    <Copy className="w-4 h-4" />
                    Duplikovat
                  </DropdownMenuItem>
                  <DropdownMenuItem className="gap-2 cursor-pointer">
                    <Share className="w-4 h-4" />
                    Sdílet
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="gap-2 cursor-pointer text-destructive focus:text-destructive">
                    <Trash2 className="w-4 h-4" />
                    Smazat
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};