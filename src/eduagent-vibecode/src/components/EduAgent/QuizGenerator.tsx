import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, XCircle, RotateCcw, Trophy, Target, Clock } from "lucide-react";

interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  topic: string;
}

interface QuizResult {
  questionId: string;
  selectedAnswer: number;
  isCorrect: boolean;
  timeSpent: number;
}

const mockQuestions: QuizQuestion[] = [
  {
    id: "1",
    question: "Která z následujících aktivit NENÍ součástí operativního managementu?",
    options: [
      "Plánování výrobní kapacity",
      "Kontrola kvality produktů", 
      "Finanční analýza investic",
      "Řízení dodavatelského řetězce"
    ],
    correctAnswer: 2,
    explanation: "Finanční analýza investic patří do oblasti finančního managementu, ne operativního managementu, který se zaměřuje na výrobní a provozní procesy.",
    topic: "Základy"
  },
  {
    id: "2",
    question: "Co charakterizuje předmětné uspořádání výroby?",
    options: [
      "Stroje jsou seskupeny podle technologických operací",
      "Produkty procházejí postupně všemi pracovišti v pořadí operací",
      "Všechny operace se provádějí na jednom místě",
      "Výroba je organizována podle zákaznických objednávek"
    ],
    correctAnswer: 1,
    explanation: "Předmětné uspořádání (výrobní linka) znamená, že produkty postupně procházejí všemi pracovišti v pořadí potřebných operací.",
    topic: "Výrobní systémy"
  },
  {
    id: "3", 
    question: "Jaký je hlavní cíl Just-in-Time (JIT) přístupu?",
    options: [
      "Maximalizace zásob pro zajištění plynulé výroby",
      "Minimalizace zásob a eliminace plýtvání",
      "Zvýšení rychlosti výroby za každou cenu",
      "Snížení kvality ve prospěch rychlosti"
    ],
    correctAnswer: 1,
    explanation: "JIT se zaměřuje na minimalizaci zásob a eliminaci všech forem plýtvání při zachování plynulosti výroby.",
    topic: "Lean management"
  }
];

export const QuizGenerator = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [results, setResults] = useState<QuizResult[]>([]);
  const [showResult, setShowResult] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [startTime] = useState(Date.now());

  const handleAnswerSelect = (answerIndex: number) => {
    setSelectedAnswer(answerIndex);
  };

  const handleNextQuestion = () => {
    if (selectedAnswer === null) return;

    const result: QuizResult = {
      questionId: mockQuestions[currentQuestion].id,
      selectedAnswer,
      isCorrect: selectedAnswer === mockQuestions[currentQuestion].correctAnswer,
      timeSpent: Date.now() - startTime
    };

    setResults(prev => [...prev, result]);
    setShowResult(true);

    setTimeout(() => {
      if (currentQuestion < mockQuestions.length - 1) {
        setCurrentQuestion(prev => prev + 1);
        setSelectedAnswer(null);
        setShowResult(false);
      } else {
        setIsCompleted(true);
      }
    }, 2000);
  };

  const resetQuiz = () => {
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setResults([]);
    setShowResult(false);
    setIsCompleted(false);
  };

  const getScore = () => {
    const correct = results.filter(r => r.isCorrect).length;
    return Math.round((correct / mockQuestions.length) * 100);
  };

  const getScoreColor = () => {
    const score = getScore();
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  if (isCompleted) {
    const score = getScore();
    const correctAnswers = results.filter(r => r.isCorrect).length;
    
    return (
      <div className="p-6 space-y-6">
        <Card className="p-8 text-center space-y-6 bg-gradient-to-br from-success/5 to-primary/5">
          <div className="space-y-4">
            <Trophy className={`w-16 h-16 mx-auto ${getScoreColor()}`} />
            <h1 className="text-3xl font-heading font-bold text-foreground">
              Kvíz dokončen!
            </h1>
            <div className="space-y-2">
              <div className={`text-5xl font-bold ${getScoreColor()}`}>
                {score}%
              </div>
              <p className="text-muted-foreground">
                {correctAnswers} z {mockQuestions.length} správných odpovědí
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 max-w-md mx-auto">
            <div className="space-y-1">
              <Target className="w-8 h-8 mx-auto text-primary" />
              <div className="text-2xl font-bold text-foreground">{correctAnswers}</div>
              <div className="text-xs text-muted-foreground">Správně</div>
            </div>
            <div className="space-y-1">
              <XCircle className="w-8 h-8 mx-auto text-destructive" />
              <div className="text-2xl font-bold text-foreground">{mockQuestions.length - correctAnswers}</div>
              <div className="text-xs text-muted-foreground">Špatně</div>
            </div>
            <div className="space-y-1">
              <Clock className="w-8 h-8 mx-auto text-warning" />
              <div className="text-2xl font-bold text-foreground">2:34</div>
              <div className="text-xs text-muted-foreground">Čas</div>
            </div>
          </div>

          <Button onClick={resetQuiz} className="gap-2">
            <RotateCcw className="w-4 h-4" />
            Zkusit znovu
          </Button>
        </Card>

        {/* Detailed Results */}
        <Card className="p-6">
          <h2 className="text-xl font-heading font-semibold mb-4">Detailní výsledky</h2>
          <ScrollArea className="max-h-96">
            <div className="space-y-4">
              {mockQuestions.map((question, index) => {
                const result = results[index];
                return (
                  <div key={question.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      {result.isCorrect ? (
                        <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                      ) : (
                        <XCircle className="w-5 h-5 text-destructive mt-0.5" />
                      )}
                      <div className="space-y-2 flex-1">
                        <p className="font-medium text-foreground">{question.question}</p>
                        <div className="space-y-1">
                          {question.options.map((option, optionIndex) => (
                            <div 
                              key={optionIndex}
                              className={`text-sm p-2 rounded ${
                                optionIndex === question.correctAnswer
                                  ? "bg-success/10 text-success"
                                  : optionIndex === result.selectedAnswer && !result.isCorrect
                                  ? "bg-destructive/10 text-destructive"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {String.fromCharCode(65 + optionIndex)}. {option}
                            </div>
                          ))}
                        </div>
                        <p className="text-sm text-muted-foreground italic">
                          {question.explanation}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </Card>
      </div>
    );
  }

  const currentQ = mockQuestions[currentQuestion];
  
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground mb-2">
            Testové otázky
          </h1>
          <p className="text-muted-foreground">
            Otázka {currentQuestion + 1} z {mockQuestions.length}
          </p>
        </div>
        
        <Badge variant="outline">{currentQ.topic}</Badge>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <Progress value={((currentQuestion) / mockQuestions.length) * 100} className="h-2" />
        <div className="text-sm text-muted-foreground text-center">
          Pokrok: {Math.round(((currentQuestion) / mockQuestions.length) * 100)}%
        </div>
      </div>

      {/* Question Card */}
      <Card className="p-8 space-y-6">
        <h2 className="text-xl font-semibold text-foreground leading-relaxed">
          {currentQ.question}
        </h2>

        <div className="space-y-3">
          {currentQ.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswerSelect(index)}
              disabled={showResult}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                showResult
                  ? index === currentQ.correctAnswer
                    ? "border-success bg-success/10 text-success"
                    : index === selectedAnswer && selectedAnswer !== currentQ.correctAnswer
                    ? "border-destructive bg-destructive/10 text-destructive"
                    : "border-muted text-muted-foreground"
                  : selectedAnswer === index
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border hover:border-primary/50 text-foreground hover:bg-muted/50"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-medium ${
                  showResult
                    ? index === currentQ.correctAnswer
                      ? "border-success bg-success text-success-foreground"
                      : index === selectedAnswer && selectedAnswer !== currentQ.correctAnswer
                      ? "border-destructive bg-destructive text-destructive-foreground"
                      : "border-muted text-muted-foreground"
                    : selectedAnswer === index
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-muted"
                }`}>
                  {String.fromCharCode(65 + index)}
                </div>
                <span>{option}</span>
              </div>
            </button>
          ))}
        </div>

        {showResult && (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-center gap-2">
              {selectedAnswer === currentQ.correctAnswer ? (
                <CheckCircle className="w-5 h-5 text-success" />
              ) : (
                <XCircle className="w-5 h-5 text-destructive" />
              )}
              <span className={`font-medium ${
                selectedAnswer === currentQ.correctAnswer ? "text-success" : "text-destructive"
              }`}>
                {selectedAnswer === currentQ.correctAnswer ? "Správně!" : "Nesprávně"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
              <strong>Vysvětlení:</strong> {currentQ.explanation}
            </p>
          </div>
        )}
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button 
          variant="outline" 
          onClick={resetQuiz}
          className="gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          Začít znovu
        </Button>
        
        <Button 
          onClick={handleNextQuestion}
          disabled={selectedAnswer === null || showResult}
          className="gap-2"
        >
          {currentQuestion === mockQuestions.length - 1 ? "Dokončit kvíz" : "Další otázka"}
        </Button>
      </div>
    </div>
  );
};