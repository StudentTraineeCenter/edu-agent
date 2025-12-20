import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BarChart3, Send, Copy, ThumbsUp, ThumbsDown, RotateCcw } from "lucide-react";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: string[];
}

interface ChatAreaProps {
  isStudioCollapsed?: boolean;
}

const mockResponses = [
  "Based on the uploaded documents, operations management focuses on the systematic design, operation, and improvement of production and delivery systems. The key principles include efficiency optimization, quality control, and resource allocation to maximize productivity while minimizing costs.",
  
  "According to your sources, there are three main types of production layouts: product layout (assembly line), process layout (functional grouping), and fixed-position layout. Each has specific advantages depending on volume, variety, and complexity of operations.",
  
  "The documents highlight that successful operations management requires balancing five key performance objectives: quality (doing things right), speed (minimizing customer waiting time), dependability (reliable delivery), flexibility (adapting to changes), and cost (achieving efficiency).",
  
  "Your materials indicate that inventory management is crucial in operations, involving decisions about what to order, when to order, and how much to order. This includes understanding different inventory types: raw materials, work-in-progress, and finished goods.",
  
  "The sources explain that capacity planning involves determining the production capacity needed to meet changing demands. This includes long-term strategic decisions about facility size and location, as well as short-term tactical decisions about workforce scheduling and equipment utilization.",
];

let responseIndex = 0;

const getRandomResponse = () => {
  const response = mockResponses[responseIndex % mockResponses.length];
  responseIndex++;
  return response;
};

export const ChatArea = ({ isStudioCollapsed }: ChatAreaProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content: "This notebook contains three sources, two of which are text excerpts and one is an audio transcript, all focusing on Operations Management. The materials provide detailed descriptions of the course organization and assessment, including references to analysis, experience, and theoretical knowledge combined with practical examples. They further define operational management as a management process leading to the creation of a product or service and present key concepts, such as production activities (material, machines, labor, information), management goals (quality, timing, costs) and measuring performance for increased productivity. The sources also classify types of products (piece, series, mass) and explain methods for distinguishing production layout, including subject-matter and technological arrangements. Special attention is paid to the relationship between production layout on order and on stock and to the concept of distribution scheduling.",
      timestamp: new Date(),
      sources: ["3 sources"]
    },
  ]);
  
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate AI response with realistic delay
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: getRandomResponse(),
        timestamp: new Date(),
        sources: ["2-3 sources"]
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1200 + Math.random() * 800); // 1.2-2s delay for realism
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-background min-w-0 overflow-hidden">
      {/* Chat Header */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          <h2 className="font-heading font-semibold text-foreground">AI Studijní asistent</h2>
        </div>
        <p className="text-sm text-muted-foreground mt-1">3 materiály načteny</p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-6">
        <div className="space-y-6 max-w-full">
          {messages.map((message) => (
            <div key={message.id} className="space-y-3">
              {message.type === "assistant" && (
                <div className="space-y-3">
                  <div className="prose prose-sm max-w-none text-foreground">
                    <p className="leading-relaxed">{message.content}</p>
                  </div>
                  
                  {message.sources && (
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {message.sources[0]}
                      </Badge>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" className="h-8 gap-2">
                      <Copy className="w-3 h-3" />
                      Kopírovat
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8">
                      <ThumbsUp className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8">
                      <ThumbsDown className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8">
                      <RotateCcw className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              )}
              
              {message.type === "user" && (
                <div className="bg-muted/50 rounded-lg p-4 ml-12">
                  <p className="text-foreground">{message.content}</p>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: "0.2s" }}></div>
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: "0.4s" }}></div>
                <span className="text-sm text-muted-foreground ml-2">Analyzuji materiály...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="px-4 pb-4">
          <div className="text-sm text-muted-foreground mb-3">Navrhované otázky:</div>
          <div className="space-y-2">
            {[
              "Jaké jsou klíčové principy operativního managementu?",
              "Jak různá výrobní uspořádání ovlivňují efektivnost?",
              "Jaké metriky definují úspěch v operativním managementu?"
            ].map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                className="w-full justify-start text-left h-auto py-2 px-3"
                onClick={() => setInput(question)}
              >
                {question}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-card">
        <div className="space-y-3">
          <div className="relative">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Zeptejte se na cokoliv o vašich materiálech..."
              className="min-h-[80px] pr-12 resize-none"
              disabled={isLoading}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              size="sm"
              className="absolute bottom-2 right-2 h-8 w-8 p-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>3 materiály</span>
            <span>Enter = odeslat, Shift+Enter = nový řádek</span>
          </div>
        </div>
      </div>
    </div>
  );
};