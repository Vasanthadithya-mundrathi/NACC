# Hugging Face MCP Birthday Hackathon Submission Guide

## 📅 Deadline
**November 30, 2025 at 11:59 PM UTC**

## ✅ Submission Checklist

### 1. Join the Organization
You must be a member of the **[MCP-1st-Birthday](https://huggingface.co/MCP-1st-Birthday)** organization on Hugging Face.
- Go to the organization page and click **"Request to join this org"**.

### 2. Prepare Your Project
Your submission should be a **Gradio app Space** on Hugging Face that functions as an MCP Server.

### 3. Create the Space
1.  Create a new Space under the `MCP-1st-Birthday` organization (or transfer it there).
2.  Select **Gradio** as the SDK.
3.  Upload your cleaned-up code (ensure `requirements.txt` is present).

### 4. Update README.md (Critical!)
Your Space's `README.md` **must** include the following:

*   **Track Tags**: Add the appropriate tag to the YAML metadata at the top of your README.
    *   `mcp-server-track` (General)
    *   `building-mcp-track-enterprise`
    *   `building-mcp-track-consumer`
    *   `building-mcp-track-creative`
*   **Video Demo**: A link to a 1-5 minute video demonstrating your MCP server in action (using Claude Desktop, Cursor, or a custom client).
*   **Social Media Proof**: A link to a post on X (Twitter) or LinkedIn about your project, tagging Hugging Face.
*   **Team Members**: If working in a team, list all Hugging Face usernames.

### 5. For Judges & Testers
To ensure judges can easily test your project:
*   **Clear Instructions**: Explain how to connect an MCP client (like Claude Desktop) to your server.
*   **Example Prompts**: Provide a list of example queries (e.g., "Navigate to Documents", "Create a file named test.txt") that show off your server's capabilities.
*   **Environment Variables**: If your server needs API keys, explain how to set them in the Space's settings.

## 🚀 Final Polish
*   Ensure all unnecessary files (logs, temp scripts) are removed (Done!).
*   Verify `requirements.txt` has all dependencies.
*   Test your Space to make sure it builds and runs correctly on Hugging Face.

Good luck! 🎉
