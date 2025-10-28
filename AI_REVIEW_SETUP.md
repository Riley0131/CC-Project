# AI Code Review Setup Instructions

Uses Gemini 2.5 flash

This guide will help you set up the AI-powered code review workflow for your GitHub repository using Google's Gemini API (FREE tier).

## Overview

The AI Code Review workflow automatically analyzes code changes using Google's Gemini AI when:
- A pull request is opened, synchronized, or reopened
- Code is pushed to the `main` or `develop` branches

## Prerequisites

- A GitHub repository with the workflow files in place
- A Google account (Gmail account)
- Repository admin access to configure secrets

## Manual Setup Steps

### 1. Get Your Free Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Get API Key** or **Create API Key**
4. Select **Create API key in new project** (or choose an existing project)
5. Copy the API key (you can always retrieve it later from AI Studio)

**Note**: The free tier includes:
- 15 requests per minute
- 1,500 requests per day
- No credit card required!

### 2. Add the API Key to GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, navigate to **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Set the following:
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: Paste your Gemini API key
6. Click **Add secret**

### 3. Configure Workflow Permissions (if needed)

If the workflow fails with permission errors, you may need to enable workflow permissions:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

### 4. Verify Workflow Files

Ensure these files exist in your repository:
- `.github/workflows/ai-review.yml` - The GitHub Actions workflow
- `ci/ai_review.py` - The Python script that performs the review

### 5. Test the Workflow

To test if everything is working:

1. Create a new branch:
   ```bash
   git checkout -b test-ai-review
   ```

2. Make a small change to any file:
   ```bash
   echo "# Test change" >> README.md
   git add README.md
   git commit -m "Test AI review workflow"
   git push -u origin test-ai-review
   ```

3. Create a pull request on GitHub

4. Check the **Actions** tab to see the workflow running

5. Once complete, check the workflow summary for the AI review

## Optional Configuration

### Customize the AI Model

By default, the workflow uses `gemini-1.5-flash` (fastest and free). To use a different model:

1. Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable**
3. Add:
   - **Name**: `AI_REVIEW_MODEL`
   - **Value**: Your preferred model (e.g., `gemini-1.5-pro`, `gemini-1.5-flash-8b`)

Available free Gemini models:
- `gemini-1.5-flash` (recommended - balanced speed and quality)
- `gemini-1.5-flash-8b` (fastest, lighter model)
- `gemini-1.5-pro` (highest quality, but slower)
- `gemini-2.0-flash-exp` (experimental next-gen model)

### Adjust Diff Size Limit

To change the maximum characters analyzed from diffs:

1. Add a repository variable named `AI_REVIEW_MAX_DIFF_CHARS`
2. Set the value (default is `12000`)

### Modify Trigger Branches

To change which branches trigger the review on push:

1. Edit `.github/workflows/ai-review.yml`
2. Modify the `push.branches` section:
   ```yaml
   push:
     branches:
       - main
       - develop
       - your-branch-name
   ```

## Troubleshooting

### Workflow doesn't run
- Check that workflow files are on the default branch
- Verify the workflow is enabled in **Actions** tab
- Ensure you're triggering the correct events (PR or push to specified branches)

### "GEMINI_API_KEY is not set" error
- Verify the secret name is exactly `GEMINI_API_KEY` (case-sensitive)
- Check that the secret is set in the repository (not organization or environment)
- Ensure you created the API key in Google AI Studio

### API rate limit errors
- Free tier allows 15 requests/minute and 1,500/day
- If you hit limits, wait a few minutes or reduce review frequency
- Consider adding conditional execution to only run on specific branches
- Check your usage at [Google AI Studio](https://aistudio.google.com/)

### Permission errors
- Enable workflow read/write permissions (see step 3 above)
- Ensure the `GITHUB_TOKEN` has necessary permissions

### Git command failures
- Ensure `fetch-depth: 0` is set in the checkout step (already configured)
- Check that the base branch exists and has commits

## Cost Considerations

**Good news: This is completely FREE!** 🎉

Google's Gemini API free tier includes:
- 15 requests per minute
- 1,500 requests per day
- No credit card required
- No charges for standard usage

This is more than enough for most repositories. Even active projects with dozens of PRs per day will stay within the free limits.

## Next Steps

Once set up, the AI reviewer will automatically:
- Analyze code changes in pull requests
- Provide feedback on potential bugs and improvements
- Suggest missing tests
- Add a summary to the workflow run summary

The review appears in:
- The workflow run logs (Actions tab)
- The workflow summary page (visible after clicking on a workflow run)

## Support

For issues or questions:
- Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
- Review the [Google AI Gemini API documentation](https://ai.google.dev/docs)
- Visit [Google AI Studio](https://aistudio.google.com/) to test your API key
- Check workflow logs in the Actions tab for detailed error messages

## Switching Back to OpenAI (Optional)

If you later want to use OpenAI instead:
1. Change `GEMINI_API_KEY` to `OPENAI_API_KEY` in workflow and script
2. Replace `google-generativeai` with `openai` package
3. Update the API calls in `ci/ai_review.py`

Note: OpenAI requires billing setup and charges per request.
