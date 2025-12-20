import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RotateCcw, ChevronLeft, ChevronRight, Eye, EyeOff, Shuffle, BookOpen } from "lucide-react";

interface Flashcard {
  id: string;
  question: string;
  answer: string;
  difficulty: "easy" | "medium" | "hard";
  topic: string;
}

const mockFlashcards: Flashcard[] = [
  {
    id: "1",
    question: "Co je operativní management?",
    answer: "Operativní management je proces řízení vedoucí k vytvoření produktu nebo služby. Zahrnuje plánování, organizování a kontrolu výrobních aktivit.",
    difficulty: "medium",
    topic: "Základy"
  },
  {
    id: "2", 
    question: "Jaké jsou 3 hlavní typy výrobního uspořádání?",
    answer: "1. Předmětné uspořádání (výrobní linka), 2. Technologické uspořádání (funkční seskupení), 3. Stacionární uspořádání (pevná pozice).",
    difficulty: "hard",
    topic: "Výrobní systémy"
  },
  {
    id: "3",
    question: "Definujte pojem 'produktivita' v kontextu operativního managementu.",
    answer: "Produktivita je poměr mezi výstupy (produkty/služby) a vstupy (zdroje). Měří efektivnost využití zdrojů při výrobě.",
    difficulty: "easy",
    topic: "Výkonnost"
  },
  {
    id: "4",
    question: "Jaké jsou 5 klíčových cílů výkonnosti v operacích?",
    answer: "1. Kvalita (správné provedení), 2. Rychlost (minimalizace čekání), 3. Spolehlivost (dodržení termínů), 4. Flexibilita (přizpůsobení změnám), 5. Náklady (efektivnost).",
    difficulty: "hard",
    topic: "Výkonnost"
  }
];

export const FlashcardsGenerator = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [cards, setCards] = useState(mockFlashcards);

  const currentCard = cards[currentIndex];

  const generateNewCards = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  };

  const shuffleCards = () => {
    const shuffled = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setCurrentIndex(0);
    setShowAnswer(false);
  };

  const nextCard = () => {
    setCurrentIndex((prev) => (prev + 1) % cards.length);
    setShowAnswer(false);
  };

  const prevCard = () => {
    setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
    setShowAnswer(false);
  };

  const getDifficultyColor = (difficulty: Flashcard["difficulty"]) => {
    switch (difficulty) {
      case "easy": return "bg-success/10 text-success border-success/20";
      case "medium": return "bg-warning/10 text-warning border-warning/20";
      case "hard": return "bg-destructive/10 text-destructive border-destructive/20";
    }
  };

  const getDifficultyText = (difficulty: Flashcard["difficulty"]) => {
    switch (difficulty) {
      case "easy": return "Snadné";
      case "medium": return "Střední";
      case "hard": return "Těžké";
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-foreground mb-2">
            Kartičky pro opakování
          </h1>
          <p className="text-muted-foreground">
            Automaticky generované z vašich studijních materiálů
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button 
            onClick={generateNewCards} 
            disabled={isGenerating}
            className="gap-2"
          >
            {isGenerating ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <RotateCcw className="w-4 h-4" />
            )}
            {isGenerating ? "Generuji..." : "Generovat nové"}
          </Button>
          <Button variant="outline" onClick={shuffleCards} className="gap-2">
            <Shuffle className="w-4 h-4" />
            Zamíchat
          </Button>
        </div>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-4">
        <div className="text-sm text-muted-foreground">
          {currentIndex + 1} z {cards.length}
        </div>
        <div className="flex-1 bg-muted rounded-full h-2">
          <div 
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / cards.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <Card className="relative min-h-[400px] p-8 bg-gradient-to-br from-card to-card/80 border-2">
        <div className="absolute top-4 right-4 flex gap-2">
          <Badge className={getDifficultyColor(currentCard.difficulty)}>
            {getDifficultyText(currentCard.difficulty)}
          </Badge>
          <Badge variant="outline">{currentCard.topic}</Badge>
        </div>

        <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center space-y-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-primary mb-4">
              <BookOpen className="w-5 h-5" />
              <span className="text-sm font-medium">Otázka</span>
            </div>
            
            <h2 className="text-xl font-semibold text-foreground leading-relaxed">
              {currentCard.question}
            </h2>
          </div>

          {showAnswer && (
            <div className="space-y-4 animate-fade-in">
              <div className="w-full h-px bg-border" />
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-success">
                  <Eye className="w-4 h-4" />
                  <span className="text-sm font-medium">Odpověď</span>
                </div>
                <p className="text-foreground leading-relaxed">
                  {currentCard.answer}
                </p>
              </div>
            </div>
          )}

          <Button 
            onClick={() => setShowAnswer(!showAnswer)}
            variant={showAnswer ? "outline" : "default"}
            className="gap-2 mt-8"
          >
            {showAnswer ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            {showAnswer ? "Skrýt odpověď" : "Zobrazit odpověď"}
          </Button>
        </div>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button 
          variant="outline" 
          onClick={prevCard}
          disabled={cards.length <= 1}
          className="gap-2"
        >
          <ChevronLeft className="w-4 h-4" />
          Předchozí
        </Button>
        
        <div className="flex gap-1">
          {cards.map((_, index) => (
            <button
              key={index}
              onClick={() => {
                setCurrentIndex(index);
                setShowAnswer(false);
              }}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentIndex ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        <Button 
          variant="outline" 
          onClick={nextCard}
          disabled={cards.length <= 1}
          className="gap-2"
        >
          Další
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};