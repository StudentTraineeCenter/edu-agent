import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Brain, 
  GitBranch, 
  ZoomIn, 
  ZoomOut, 
  Download, 
  Share, 
  RotateCcw,
  Maximize,
  ChevronRight,
  Circle
} from "lucide-react";

interface MindMapNode {
  id: string;
  title: string;
  level: number;
  children: MindMapNode[];
  color: string;
}

const mockMindMap: MindMapNode = {
  id: "root",
  title: "Operativní Management", 
  level: 0,
  color: "bg-primary",
  children: [
    {
      id: "1",
      title: "Výrobní systémy",
      level: 1,
      color: "bg-blue-500",
      children: [
        {
          id: "1.1",
          title: "Předmětné uspořádání",
          level: 2,
          color: "bg-blue-400",
          children: [
            { id: "1.1.1", title: "Výrobní linka", level: 3, color: "bg-blue-300", children: [] },
            { id: "1.1.2", title: "Sériová výroba", level: 3, color: "bg-blue-300", children: [] }
          ]
        },
        {
          id: "1.2", 
          title: "Technologické uspořádání",
          level: 2,
          color: "bg-blue-400",
          children: [
            { id: "1.2.1", title: "Funkční seskupení", level: 3, color: "bg-blue-300", children: [] },
            { id: "1.2.2", title: "Flexibilní výroba", level: 3, color: "bg-blue-300", children: [] }
          ]
        },
        {
          id: "1.3",
          title: "Stacionární uspořádání", 
          level: 2,
          color: "bg-blue-400",
          children: [
            { id: "1.3.1", title: "Zakázková výroba", level: 3, color: "bg-blue-300", children: [] },
            { id: "1.3.2", title: "Komplexní projekty", level: 3, color: "bg-blue-300", children: [] }
          ]
        }
      ]
    },
    {
      id: "2",
      title: "Výkonnostní cíle",
      level: 1, 
      color: "bg-green-500",
      children: [
        { id: "2.1", title: "Kvalita", level: 2, color: "bg-green-400", children: [] },
        { id: "2.2", title: "Rychlost", level: 2, color: "bg-green-400", children: [] },
        { id: "2.3", title: "Spolehlivost", level: 2, color: "bg-green-400", children: [] },
        { id: "2.4", title: "Flexibilita", level: 2, color: "bg-green-400", children: [] },
        { id: "2.5", title: "Náklady", level: 2, color: "bg-green-400", children: [] }
      ]
    },
    {
      id: "3",
      title: "Kapacitní plánování",
      level: 1,
      color: "bg-purple-500", 
      children: [
        {
          id: "3.1",
          title: "Dlouhodobé plánování",
          level: 2,
          color: "bg-purple-400",
          children: [
            { id: "3.1.1", title: "Lokalizace zařízení", level: 3, color: "bg-purple-300", children: [] },
            { id: "3.1.2", title: "Velikost kapacity", level: 3, color: "bg-purple-300", children: [] }
          ]
        },
        {
          id: "3.2",
          title: "Krátkodobé plánování", 
          level: 2,
          color: "bg-purple-400",
          children: [
            { id: "3.2.1", title: "Plánování pracovní síly", level: 3, color: "bg-purple-300", children: [] },
            { id: "3.2.2", title: "Využití strojů", level: 3, color: "bg-purple-300", children: [] }
          ]
        }
      ]
    },
    {
      id: "4", 
      title: "Řízení zásob",
      level: 1,
      color: "bg-orange-500",
      children: [
        { id: "4.1", title: "Suroviny", level: 2, color: "bg-orange-400", children: [] },
        { id: "4.2", title: "Nedokončená výroba", level: 2, color: "bg-orange-400", children: [] },
        { id: "4.3", title: "Hotové výrobky", level: 2, color: "bg-orange-400", children: [] },
        { id: "4.4", title: "EOQ model", level: 2, color: "bg-orange-400", children: [] }
      ]
    }
  ]
};

export const MindMap = () => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(["root", "1", "2", "3", "4"]));
  const [zoom, setZoom] = useState(100);

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderNode = (node: MindMapNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children.length > 0;
    const isSelected = selectedNode === node.id;

    return (
      <div key={node.id} className={`${depth > 0 ? 'ml-6' : ''}`}>
        <div 
          className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all hover:bg-muted/50 ${
            isSelected ? 'bg-primary/10 border border-primary/20' : ''
          }`}
          onClick={() => setSelectedNode(node.id)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.id);
              }}
              className="p-1 hover:bg-muted rounded"
            >
              <ChevronRight 
                className={`w-4 h-4 transition-transform ${
                  isExpanded ? 'rotate-90' : ''
                }`} 
              />
            </button>
          )}
          
          {!hasChildren && <div className="w-6" />}
          
          <div 
            className={`w-3 h-3 rounded-full ${node.color}`}
          />
          
          <span 
            className={`font-medium ${
              node.level === 0 ? 'text-lg' : 
              node.level === 1 ? 'text-base' : 'text-sm'
            } ${isSelected ? 'text-primary' : 'text-foreground'}`}
          >
            {node.title}
          </span>
          
          {node.level === 0 && (
            <Badge variant="outline" className="ml-2">
              Hlavní téma
            </Badge>
          )}
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const getSelectedNodeInfo = () => {
    const findNode = (node: MindMapNode): MindMapNode | null => {
      if (node.id === selectedNode) return node;
      for (const child of node.children) {
        const found = findNode(child);
        if (found) return found;
      }
      return null;
    };
    
    return findNode(mockMindMap);
  };

  const selectedNodeInfo = getSelectedNodeInfo();

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground mb-2">
            Myšlenková mapa
          </h1>
          <p className="text-muted-foreground">
            Vizualizace klíčových konceptů z vašich materiálů
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Share className="w-4 h-4" />
            Sdílet
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <RotateCcw className="w-4 h-4" />
            Regenerovat
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mind Map Tree View */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-semibold text-foreground">Struktura</h3>
              </div>
              
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setZoom(Math.max(50, zoom - 10))}
                  disabled={zoom <= 50}
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-sm text-muted-foreground px-2">
                  {zoom}%
                </span>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setZoom(Math.min(200, zoom + 10))}
                  disabled={zoom >= 200}
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <ScrollArea className="h-96">
              <div style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}>
                {renderNode(mockMindMap)}
              </div>
            </ScrollArea>
          </Card>
        </div>

        {/* Node Details */}
        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Detail uzlu</h3>
            
            {selectedNodeInfo ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full ${selectedNodeInfo.color}`} />
                  <div>
                    <h4 className="font-medium text-foreground">{selectedNodeInfo.title}</h4>
                    <p className="text-sm text-muted-foreground">
                      Úroveň {selectedNodeInfo.level + 1}
                    </p>
                  </div>
                </div>

                {selectedNodeInfo.children.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-foreground mb-2">
                      Podkategorie ({selectedNodeInfo.children.length})
                    </h5>
                    <div className="space-y-1">
                      {selectedNodeInfo.children.map(child => (
                        <div key={child.id} className="flex items-center gap-2 text-sm">
                          <Circle className="w-2 h-2 fill-current text-muted-foreground" />
                          <span className="text-muted-foreground">{child.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Button size="sm" variant="outline" className="w-full gap-2">
                    <GitBranch className="w-4 h-4" />
                    Rozbalit vše
                  </Button>
                  <Button size="sm" variant="outline" className="w-full gap-2">
                    <Maximize className="w-4 h-4" />
                    Zaměřit na uzel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Klikněte na uzel pro zobrazení detailů</p>
              </div>
            )}
          </Card>

          {/* Legend */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Legenda</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-primary" />
                <span className="text-sm text-muted-foreground">Hlavní téma</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-blue-500" />
                <span className="text-sm text-muted-foreground">Výrobní systémy</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-green-500" />
                <span className="text-sm text-muted-foreground">Výkonnostní cíle</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-purple-500" />
                <span className="text-sm text-muted-foreground">Kapacitní plánování</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full bg-orange-500" />
                <span className="text-sm text-muted-foreground">Řízení zásob</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};