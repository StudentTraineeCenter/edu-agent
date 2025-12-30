Název projektu: EduAgent: AI-powered vzdělávací platforma
Název projektu (anglicky): EduAgent: AI-powered educational platform

Tagy: Azure; Typescript; Python; FastAPI; React; LLM; RAG; LangGraph; PostgreSQL; Supabase

Odkaz na repositář (pokud není, nech prázdné): https://github.com/StudentTraineeCenter/edu-agent.git
Odkaz na výsledek (pokud není, nech prázdné):

---

Anotace projektu: V éře informačního přetížení čelí studenti náročné výzvě: efektivně zpracovat a trvale si osvojit rozsáhlé objemy studijních materiálů. Průzkum potřeb provedený mezi 25 studenty identifikoval jako klíčové bariéry obtížné zapamatování pojmů, udržení motivace a efektivní organizaci času. Jako odpověď na tyto problémy jsem vyvinul EduAgent – pokročilou vzdělávací platformu poháněnou Large Language Modely (LLM), která transformuje pasivní studijní materiály na interaktivní a personalizovanou vzdělávací zkušenost. Systém automatizuje zpracování studijních podkladů s využitím Azure Content Understanding a vektorové databáze PostgreSQL. Zásadní inovací je implementace personalizovaného studijního plánu, který se dynamicky adaptuje na základě úspěšnosti studenta. Srdcem systému je autonomní AI agent postavený na frameworku LangGraph, kombinující techniky RAG a „tool calling”, což studentům šetří čas a umožňuje jim soustředit se na samotné učení.

---

Paper: assets/EduAgent_paper.pdf

Obrázky, screenshoty, videa:
 - assets/screenshots/eduagent-dashboard.png
 - assets/screenshots/eduagent-ai-content.png
 - assets/screenshots/eduagent-ai-response.png
 - assets/screenshots/eduagent-flashcard.png
 - assets/screenshots/eduagent-quiz.png
 - assets/screenshots/eduagent-study-plan.png
 - assets/screenshots/eduagent-note.png
 - assets/screenshots/eduagent-tool-calling.png
 - assets/screenshots/eduagent-settings.png

Reflexe: assets/EduAgent_reflexe.pdf

Soubory (popiš soubory a složky, které jsi přiložil)
 - src/ - Zdrojové kódy aplikace (FastAPI backend, React frontend, background worker)
 - assets/ - Klíčové dokumenty a ukázková data
   - EduAgent_paper.pdf - Odborná práce (paper)
   - EduAgent_reflexe.pdf - Reflexe projektu
   - EduAgent_specification.pdf - Technická specifikace
   - sample_data/ - Ukázkové studijní materiály pro testování
   - screenshots/ - Snímky obrazovky z uživatelského rozhraní
 - docs/ - Podrobná dokumentace architektury, funkcí a lokálního vývoje
 - deploy/ - Infrastruktura jako kód (Terraform) pro nasazení do Azure
 - docker-compose.yaml - Konfigurace pro lokální spuštění celého stacku

