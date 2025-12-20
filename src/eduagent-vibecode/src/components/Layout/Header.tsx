import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings, Share, User, Grid3X3 } from "lucide-react";

interface HeaderProps {
  projectTitle: string;
  isPublic?: boolean;
}

export const Header = ({ projectTitle, isPublic = false }: HeaderProps) => {
  return (
    <header className="h-header bg-card border-b border-border px-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-semibold text-sm">N</span>
          </div>
          <div className="flex items-center gap-2">
            <h1 className="font-heading font-semibold text-foreground">{projectTitle}</h1>
            {isPublic && (
              <Badge variant="secondary" className="text-xs">
                Public
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" className="gap-2">
          <Share className="w-4 h-4" />
          Share
        </Button>
        <Button variant="ghost" size="sm">
          <Settings className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Grid3X3 className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" className="w-8 h-8 rounded-full p-0">
          <User className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
};