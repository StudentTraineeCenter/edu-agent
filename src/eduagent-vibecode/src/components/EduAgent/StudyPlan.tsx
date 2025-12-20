import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Calendar, 
  Clock, 
  Target, 
  TrendingUp, 
  BookOpen, 
  CheckCircle, 
  AlertCircle,
  BarChart3,
  Brain,
  Trophy,
  Flame
} from "lucide-react";

interface StudyTask {
  id: string;
  title: string;
  type: "reading" | "flashcards" | "quiz" | "practice";
  duration: number; // minutes
  difficulty: "easy" | "medium" | "hard";
  completed: boolean;
  dueDate: string;
  topic: string;
}

interface StudyStats {
  totalStudyTime: number;
  completedTasks: number;
  totalTasks: number;
  streakDays: number;
  averageScore: number;
}

const mockTasks: StudyTask[] = [
  {
    id: "1",
    title: "Přečíst kapitolu: Typy výrobního uspořádání",
    type: "reading",
    duration: 25,
    difficulty: "medium", 
    completed: true,
    dueDate: "2024-01-20",
    topic: "Výrobní systémy"
  },
  {
    id: "2",
    title: "Kartičky: Základní pojmy operativního managementu",
    type: "flashcards",
    duration: 15,
    difficulty: "easy",
    completed: true,
    dueDate: "2024-01-20",
    topic: "Základy"
  },
  {
    id: "3",
    title: "Kvíz: Výkonnostní cíle v operacích",
    type: "quiz", 
    duration: 20,
    difficulty: "hard",
    completed: false,
    dueDate: "2024-01-21",
    topic: "Výkonnost"
  },
  {
    id: "4",
    title: "Praktická úloha: Analýza výrobní kapacity",
    type: "practice",
    duration: 45,
    difficulty: "hard",
    completed: false,
    dueDate: "2024-01-22",
    topic: "Kapacitní plánování"
  },
  {
    id: "5",
    title: "Kartičky: Lean management principy",
    type: "flashcards",
    duration: 20,
    difficulty: "medium",
    completed: false,
    dueDate: "2024-01-23",
    topic: "Lean management"
  }
];

const mockStats: StudyStats = {
  totalStudyTime: 180, // minutes this week
  completedTasks: 8,
  totalTasks: 12,
  streakDays: 5,
  averageScore: 78
};

export const StudyPlan = () => {
  const [tasks, setTasks] = useState(mockTasks);
  const [selectedDate, setSelectedDate] = useState("2024-01-21");

  const toggleTaskCompletion = (taskId: string) => {
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, completed: !task.completed } : task
    ));
  };

  const getTaskIcon = (type: StudyTask["type"]) => {
    switch (type) {
      case "reading": return <BookOpen className="w-4 h-4" />;
      case "flashcards": return <Brain className="w-4 h-4" />;
      case "quiz": return <Target className="w-4 h-4" />;
      case "practice": return <BarChart3 className="w-4 h-4" />;
    }
  };

  const getTypeLabel = (type: StudyTask["type"]) => {
    switch (type) {
      case "reading": return "Čtení";
      case "flashcards": return "Kartičky";
      case "quiz": return "Kvíz";
      case "practice": return "Cvičení";
    }
  };

  const getDifficultyColor = (difficulty: StudyTask["difficulty"]) => {
    switch (difficulty) {
      case "easy": return "bg-success/10 text-success border-success/20";
      case "medium": return "bg-warning/10 text-warning border-warning/20";
      case "hard": return "bg-destructive/10 text-destructive border-destructive/20";
    }
  };

  const getDifficultyLabel = (difficulty: StudyTask["difficulty"]) => {
    switch (difficulty) {
      case "easy": return "Snadné";
      case "medium": return "Střední";
      case "hard": return "Těžké";
    }
  };

  const todayTasks = tasks.filter(task => task.dueDate === selectedDate);
  const completedToday = todayTasks.filter(task => task.completed).length;
  const overdueTasks = tasks.filter(task => 
    new Date(task.dueDate) < new Date(selectedDate) && !task.completed
  ).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground mb-2">
            Studijní plán
          </h1>
          <p className="text-muted-foreground">
            Personalizovaný plán na základě vašeho pokroku
          </p>
        </div>
      </div>

      <Tabs defaultValue="today" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="today">Dnes</TabsTrigger>
          <TabsTrigger value="week">Týden</TabsTrigger>
          <TabsTrigger value="stats">Statistiky</TabsTrigger>
        </TabsList>

        <TabsContent value="today" className="space-y-6">
          {/* Today Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Calendar className="w-8 h-8 text-primary" />
                <div>
                  <div className="text-2xl font-bold text-foreground">{todayTasks.length}</div>
                  <div className="text-sm text-muted-foreground">Úkoly dnes</div>
                </div>
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-8 h-8 text-success" />
                <div>
                  <div className="text-2xl font-bold text-foreground">{completedToday}</div>
                  <div className="text-sm text-muted-foreground">Dokončeno</div>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-8 h-8 text-destructive" />
                <div>
                  <div className="text-2xl font-bold text-foreground">{overdueTasks}</div>
                  <div className="text-sm text-muted-foreground">Po termínu</div>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <Flame className="w-8 h-8 text-warning" />
                <div>
                  <div className="text-2xl font-bold text-foreground">{mockStats.streakDays}</div>
                  <div className="text-sm text-muted-foreground">Dní v řadě</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Daily Progress */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">Dnešní pokrok</h3>
              <Badge variant="outline">{completedToday}/{todayTasks.length} dokončeno</Badge>
            </div>
            <Progress 
              value={todayTasks.length > 0 ? (completedToday / todayTasks.length) * 100 : 0} 
              className="h-3 mb-2"
            />
            <p className="text-sm text-muted-foreground">
              {todayTasks.length > 0 
                ? `${Math.round((completedToday / todayTasks.length) * 100)}% úkolů dokončeno`
                : "Žádné úkoly na dnes"
              }
            </p>
          </Card>

          {/* Today's Tasks */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Dnešní úkoly</h3>
            <ScrollArea className="max-h-96">
              <div className="space-y-3">
                {todayTasks.map((task) => (
                  <div 
                    key={task.id}
                    className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                      task.completed 
                        ? "bg-success/5 border-success/20" 
                        : "bg-card hover:bg-muted/50 border-border"
                    }`}
                  >
                    <button
                      onClick={() => toggleTaskCompletion(task.id)}
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                        task.completed
                          ? "bg-success border-success text-success-foreground"
                          : "border-muted hover:border-primary"
                      }`}
                    >
                      {task.completed && <CheckCircle className="w-4 h-4" />}
                    </button>

                    <div className="flex items-center gap-2">
                      {getTaskIcon(task.type)}
                      <div className="flex-1">
                        <h4 className={`font-medium ${
                          task.completed ? "line-through text-muted-foreground" : "text-foreground"
                        }`}>
                          {task.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {getTypeLabel(task.type)}
                          </Badge>
                          <Badge className={`text-xs ${getDifficultyColor(task.difficulty)}`}>
                            {getDifficultyLabel(task.difficulty)}
                          </Badge>
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.duration} min
                          </span>
                        </div>
                      </div>
                    </div>

                    <Badge variant="outline">{task.topic}</Badge>
                  </div>
                ))}
                
                {todayTasks.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Trophy className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Všechny úkoly dokončeny! 🎉</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="week" className="space-y-6">
          {/* Weekly Overview */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Týdenní přehled</h3>
            <div className="grid grid-cols-7 gap-2">
              {["Po", "Út", "St", "Čt", "Pá", "So", "Ne"].map((day, index) => {
                const dayTasks = tasks.filter(task => {
                  const taskDate = new Date(task.dueDate);
                  const dayOfWeek = taskDate.getDay();
                  return dayOfWeek === (index + 1) % 7;
                });
                const completedDayTasks = dayTasks.filter(task => task.completed).length;
                
                return (
                  <div key={day} className="text-center">
                    <div className="text-sm font-medium text-muted-foreground mb-2">{day}</div>
                    <div className="h-20 bg-muted/30 rounded-lg flex flex-col items-center justify-center">
                      <div className="text-lg font-bold text-foreground">{dayTasks.length}</div>
                      <div className="text-xs text-muted-foreground">
                        {completedDayTasks}/{dayTasks.length}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* All Tasks */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Všechny úkoly</h3>
            <ScrollArea className="max-h-96">
              <div className="space-y-3">
                {tasks.map((task) => (
                  <div 
                    key={task.id}
                    className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                      task.completed 
                        ? "bg-success/5 border-success/20" 
                        : new Date(task.dueDate) < new Date(selectedDate)
                        ? "bg-destructive/5 border-destructive/20"
                        : "bg-card hover:bg-muted/50 border-border"
                    }`}
                  >
                    <button
                      onClick={() => toggleTaskCompletion(task.id)}
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                        task.completed
                          ? "bg-success border-success text-success-foreground"
                          : "border-muted hover:border-primary"
                      }`}
                    >
                      {task.completed && <CheckCircle className="w-4 h-4" />}
                    </button>

                    <div className="flex items-center gap-2 flex-1">
                      {getTaskIcon(task.type)}
                      <div className="flex-1">
                        <h4 className={`font-medium ${
                          task.completed ? "line-through text-muted-foreground" : "text-foreground"
                        }`}>
                          {task.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {getTypeLabel(task.type)}
                          </Badge>
                          <Badge className={`text-xs ${getDifficultyColor(task.difficulty)}`}>
                            {getDifficultyLabel(task.difficulty)}
                          </Badge>
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.duration} min
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(task.dueDate).toLocaleDateString('cs-CZ')}
                          </span>
                        </div>
                      </div>
                    </div>

                    <Badge variant="outline">{task.topic}</Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        </TabsContent>

        <TabsContent value="stats" className="space-y-6">
          {/* Study Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-6 text-center">
              <Clock className="w-8 h-8 text-primary mx-auto mb-3" />
              <div className="text-2xl font-bold text-foreground mb-1">
                {Math.floor(mockStats.totalStudyTime / 60)}h {mockStats.totalStudyTime % 60}m
              </div>
              <div className="text-sm text-muted-foreground">Studium tento týden</div>
            </Card>

            <Card className="p-6 text-center">
              <Target className="w-8 h-8 text-success mx-auto mb-3" />
              <div className="text-2xl font-bold text-foreground mb-1">
                {mockStats.completedTasks}/{mockStats.totalTasks}
              </div>
              <div className="text-sm text-muted-foreground">Úkolů dokončeno</div>
            </Card>

            <Card className="p-6 text-center">
              <TrendingUp className="w-8 h-8 text-warning mx-auto mb-3" />
              <div className="text-2xl font-bold text-foreground mb-1">
                {mockStats.averageScore}%
              </div>
              <div className="text-sm text-muted-foreground">Průměrné skóre</div>
            </Card>

            <Card className="p-6 text-center">
              <Flame className="w-8 h-8 text-destructive mx-auto mb-3" />
              <div className="text-2xl font-bold text-foreground mb-1">
                {mockStats.streakDays}
              </div>
              <div className="text-sm text-muted-foreground">Dní studium v řadě</div>
            </Card>
          </div>

          {/* Study Goal Progress */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Týdenní cíl</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Studium: 5 hodin týdně</span>
                <span className="text-sm font-medium text-foreground">
                  {Math.floor(mockStats.totalStudyTime / 60)}h z 5h
                </span>
              </div>
              <Progress value={(mockStats.totalStudyTime / (5 * 60)) * 100} className="h-3" />
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Úkoly: 12 za týden</span>
                <span className="text-sm font-medium text-foreground">
                  {mockStats.completedTasks} z {mockStats.totalTasks}
                </span>
              </div>
              <Progress value={(mockStats.completedTasks / mockStats.totalTasks) * 100} className="h-3" />
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};