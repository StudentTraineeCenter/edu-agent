from pydantic import BaseModel, Field


class UsageLimitDto(BaseModel):
    """DTO for usage limit information."""

    used: int = Field(description="Number of operations used today")
    limit: int = Field(description="Maximum number of operations allowed per day")


class UsageDto(BaseModel):
    """DTO for user usage statistics."""

    chat_messages: UsageLimitDto = Field(description="Chat message usage statistics")
    flashcard_generations: UsageLimitDto = Field(
        description="Flashcard generation usage statistics"
    )
    quiz_generations: UsageLimitDto = Field(
        description="Quiz generation usage statistics"
    )
    document_uploads: UsageLimitDto = Field(
        description="Document upload usage statistics"
    )


class UsageResponse(BaseModel):
    """Response model for usage statistics."""

    usage: UsageDto = Field(description="User usage statistics")

