# Privacy Policy for EduAgent Testing

**Last Updated:** 22.11.2025

**Effective Date:** 22.11.2025

## Introduction

This Privacy Policy describes how we collect, use, and protect your personal information when you participate in testing the EduAgent application. This application is currently in a testing phase and uses Microsoft Azure Active Directory (Azure AD) for authentication.

## Scope

This privacy policy applies to all testers who access the EduAgent application using their personal Microsoft accounts. By signing in and using the application, you acknowledge that you have read and understood this privacy policy.

## Information We Collect

### Account Information

When you sign in with your Microsoft account, we collect the following information from your Microsoft account:

- **Azure Object ID (OID)**: A unique identifier assigned by Microsoft Azure AD
- **Email Address**: Your Microsoft account email address
- **Name**: Your display name from your Microsoft account (may include given name and family name)
- **Account Creation Timestamp**: The date and time when your account was first created in our system

### User-Generated Content

When you use the application, we store the following content associated with your account:

- **Projects**: Learning projects you create, including project names, descriptions, and language preferences
- **Documents**: Files you upload (PDF, DOCX, TXT, RTF), including:
  - Original document files stored in Azure Blob Storage
  - Extracted text content and summaries
  - Document segments and vector embeddings for search functionality
- **Chats**: Conversation history with the AI tutor, including:
  - Your messages
  - AI responses
  - Document citations used in responses
  - Tool calls made during conversations
- **Quizzes**: AI-generated quizzes and quiz questions you create
- **Flashcards**: AI-generated flashcard groups and individual flashcards
- **Study Attempts**: Records of your study progress, including:
  - Items studied (flashcards or quiz questions)
  - Your answers
  - Correctness of answers
  - Topics covered
- **Usage Statistics**: Daily usage counters for:
  - Chat messages sent
  - Flashcard groups generated
  - Quizzes generated
  - Documents uploaded

## How We Use Your Information

### Account Management

- To authenticate and identify you when you access the application
- To associate your content (projects, documents, chats, etc.) with your account
- To provide personalized experiences based on your project language preferences

### Application Functionality

- To process and store documents you upload
- To generate AI-powered content (quizzes, flashcards, chat responses) based on your documents
- To enable document search and retrieval within your projects
- To track your study progress and usage statistics
- To enforce daily usage limits

### Service Improvement

- To monitor application performance and identify issues
- To improve AI model responses and content generation quality
- To analyze usage patterns (in aggregate, anonymized form)

## Third-Party Services

We use the following third-party services that may process your data:

### Microsoft Azure Services

- **Azure Active Directory (Entra ID)**: For user authentication and identity management

  - We request the following permissions: `openid`, `profile`, `email`
  - Microsoft handles the authentication process
  - We only receive the information listed in the "Account Information" section above

- **Azure Blob Storage**: For storing your uploaded documents

  - Documents are stored securely in Azure cloud storage
  - Only accessible to authenticated users who own the documents

- **Azure OpenAI**: For AI-powered features including:

  - Document text extraction and summarization
  - Quiz generation
  - Flashcard generation
  - Chat responses and tutoring
  - Document content is sent to Azure OpenAI for processing

- **Azure Content Understanding**: For document processing
  - Documents are analyzed to extract structured content
  - Summaries are automatically generated

### Database Storage

- **PostgreSQL Database**: For storing:
  - User account information
  - Project and content metadata
  - Chat history
  - Quiz and flashcard data
  - Study attempt records
  - Usage statistics
  - Document embeddings for search functionality

## Data Security

We implement appropriate technical and organizational measures to protect your personal information:

- **Authentication**: Access requires Microsoft account authentication
- **Authorization**: Users can only access their own data
- **Encryption**: Data in transit is encrypted using HTTPS/TLS
- **Secure Storage**: Documents stored in Azure Blob Storage with access controls
- **Database Security**: Database access is restricted and secured
- **Token Security**: Authentication tokens are validated and verified

## Data Sharing and Disclosure

We do not sell, trade, or rent your personal information to third parties. We may share your data only in the following circumstances:

### Service Providers

- **Microsoft Azure**: As described above, your data is processed and stored on Microsoft Azure infrastructure
- **Azure OpenAI**: Document content is sent to Azure OpenAI for AI processing (quiz generation, flashcard creation, chat responses)
- **Azure Content Understanding**: Documents are sent for text extraction and analysis

### Legal Requirements

We may disclose your information if required by law or in response to valid legal requests.

### No Cross-User Sharing

- Your projects, documents, chats, quizzes, and flashcards are private to your account
- Other users cannot access your content
- We do not share your data with other testers or users

## Your Rights and Choices

### Access Your Data

You can access your account information through the application's user profile endpoint.

### Delete Your Data

You can delete your content at any time:

- Delete individual projects (which removes all associated content)
- Delete individual documents
- Delete chats, quizzes, and flashcard groups
- Contact us to request complete account deletion

### Account Deletion

To request complete deletion of your account and all associated data, please contact the testing administrators. Note that:

- Account deletion will remove all your projects, documents, chats, quizzes, flashcards, and study attempts
- Some data may be retained in backups for a limited period
- Deletion requests will be processed within a reasonable timeframe

### Usage Limits

The application enforces daily usage limits. You can view your current usage statistics through the application.

## Data Retention

- **Active Accounts**: Data is retained as long as your account is active
- **Deleted Accounts**: Upon account deletion, data is removed from active systems
- **Backups**: Some data may remain in backups for a limited period (typically 30-90 days) before being permanently deleted
- **Logs**: Application logs may be retained for troubleshooting and security purposes

## Children's Privacy

This application is not intended for users under the age of 13. We do not knowingly collect personal information from children under 13. If you are a parent or guardian and believe your child has provided us with personal information, please contact us to have that information removed.

## International Data Transfers

Your data may be processed and stored on Microsoft Azure servers located outside your country of residence. By using this application, you consent to the transfer of your data to these locations.

## Testing Environment Notice

**Important**: This application is currently in a testing phase. As such:

- Data may be reset or cleared during testing periods
- Features may change without notice
- Some data may be used for testing and debugging purposes
- The application may not be available at all times
- We recommend not uploading highly sensitive or confidential documents during testing

## Changes to This Privacy Policy

We may update this Privacy Policy from time to time. We will notify testers of any material changes by:

- Posting the updated policy in the application documentation
- Updating the "Last Updated" date at the top of this policy

Your continued use of the application after changes become effective constitutes acceptance of the updated policy.

## Contact Information

If you have questions, concerns, or requests regarding this Privacy Policy or your personal information, please contact:

- **Testing Administrators**: Richard Amare
- **Email**: richard.amare@studentstc.cz

## Microsoft Privacy Statement

Since this application uses Microsoft Azure AD for authentication, your use of Microsoft services is also subject to Microsoft's privacy policies:

- [Microsoft Privacy Statement](https://privacy.microsoft.com/privacystatement)
- [Microsoft Services Agreement](https://www.microsoft.com/legal/terms-of-use)

## Consent

By signing in to the EduAgent application with your Microsoft account, you consent to:

1. The collection and use of your information as described in this Privacy Policy
2. The processing of your documents by Azure OpenAI and Azure Content Understanding
3. The storage of your data on Microsoft Azure infrastructure
4. The use of your data for application functionality and service improvement

If you do not agree with this Privacy Policy, please do not use the application.

## Summary

**What we collect:**

- Basic account info (OID, email, name) from your Microsoft account
- Content you create (projects, documents, chats, quizzes, flashcards)
- Study progress and usage statistics

**How we use it:**

- To provide the application functionality
- To generate AI-powered content based on your documents
- To track your progress and enforce usage limits

**Who we share with:**

- Microsoft Azure (hosting and authentication)
- Azure OpenAI (AI processing)
- Azure Content Understanding (document processing)
- No sharing with other users

**Your rights:**

- Access your data
- Delete your content
- Request account deletion
- View usage statistics

**Security:**

- Microsoft authentication required
- Encrypted data transmission
- Secure cloud storage
- Access controls in place

---

_This Privacy Policy is specific to the testing phase of the EduAgent application. A revised policy will be provided if and when the application moves to production._
