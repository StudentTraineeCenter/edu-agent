from core.agents.flashcard import build_flashcard_tools
from core.agents.llm import make_llm_streaming
from core.agents.quiz import build_quiz_tools
from core.agents.rag import make_project_retrieval_tool
from core.agents.search import SearchInterface
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def make_agent(
    language_code: str, project_id: str, search_interface: SearchInterface
) -> AgentExecutor:
    retrieval_tool = make_project_retrieval_tool(project_id, search_interface)

    flashcard_tools = build_flashcard_tools(search_interface=search_interface)
    quiz_tools = build_quiz_tools(search_interface=search_interface)

    system = f"""You are a helpful AI assistant. Always respond in {language_code}.

TOOL SELECTION POLICY:
- If the user asks to create flashcards (e.g., "make flashcards", "anki cards", "create cards"):
  1) If the input references specific documents (mentions like "from this/that/these/those" or bracket indices like [1], [3]),
     FIRST call the retrieval tool to identify the documents, then call flashcards_create_scoped with those document_ids.
  2) Otherwise, call flashcards_create with a sensible count (default 15-30) and any user preferences (difficulty, focus topic).
- If the user asks to create a quiz (e.g., "quiz", "MCQ", "multiple choice"):
  1) If the input references documents as above, FIRST call retrieval, then call quiz_create_scoped with document_ids.
  2) Otherwise, call quiz_create with a sensible count (default 10-30) and any user preferences.
- If the user asks general questions about project content, CALL the retrieval tool first and answer with citations.
- When using retrieved content in answers, add inline [n] citations immediately after the sentence.
- If there is no relevant context, say you don't know rather than guessing.

RESPONSE BEHAVIOR:
- When flashcards or quizzes are successfully created, the tools will return a message field with the success message and count.
- Simply repeat the message from the tool output - it already contains the proper success message with count.
- DO NOT display any raw JSON data, tool outputs, or technical details to the user.
- DO NOT include any backticks, code blocks, or markdown formatting in your response.
- The tool outputs already contain user-friendly messages like "✅ Flashcards created successfully! I've generated X flashcards for you. You can now start studying them."
- Just pass through the message from the tool output as your response.
- Your response should be plain text only - no formatting, no code blocks, no backticks.

SCOPING RULES:
- The retrieval tool returns "sources" including citation_index and document_id fields.
- When the user references [n] indices or uses pronouns (this/that/these/those), map those to "document_id"s from the latest retrieval call and pass them to the scoped tool.
- If the user specifies a focus topic like "focus on definitions", pass it as a user_prompt or a short query string to bias selection.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    tools = [retrieval_tool] + flashcard_tools + quiz_tools

    llm = make_llm_streaming()
    agent = create_openai_tools_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=8,
    )
