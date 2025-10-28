# AI Code Review Setup Instructions

This guide will help you set up the AI-powered code review workflow for your GitHub repository.

## Overview

The AI Code Review workflow automatically analyzes code changes using OpenAI's GPT models when:
- A pull request is opened, synchronized, or reopened
- Code is pushed to the `main` or `develop` branches

## Prerequisites

- A GitHub repository with the workflow files in place
- An OpenAI API account with API access
- Repository admin access to configure secrets

## Manual Setup Steps

### 1. Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the API key (you won't be able to see it again)

### 2. Add the API Key to GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, navigate to **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Set the following:
   - **Name**: `OPENAI_API_KEY`
   - **Secret**: Paste your OpenAI API key
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

By default, the workflow uses `gpt-4o-mini`. To use a different model:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** or **New variable**
3. Add:
   - **Name**: `AI_REVIEW_MODEL`
   - **Value**: Your preferred model (e.g., `gpt-4o`, `gpt-4-turbo`)

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

### "OPENAI_API_KEY is not set" error
- Verify the secret name is exactly `OPENAI_API_KEY` (case-sensitive)
- Check that the secret is set in the repository (not organization or environment)

### API rate limit errors
- Check your OpenAI account usage and billing
- Consider using a different model or reducing review frequency
- Add rate limiting or conditional execution to the workflow

### Permission errors
- Enable workflow read/write permissions (see step 3 above)
- Ensure the `GITHUB_TOKEN` has necessary permissions

### Git command failures
- Ensure `fetch-depth: 0` is set in the checkout step (already configured)
- Check that the base branch exists and has commits

## Cost Considerations

- Each review consumes OpenAI API tokens
- `gpt-4o-mini` is the most cost-effective option (~$0.15 per million input tokens)
- Monitor your OpenAI usage dashboard regularly
- Consider limiting the workflow to only pull requests if costs are a concern

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
- Review the [OpenAI API documentation](https://platform.openai.com/docs)
- Check workflow logs in the Actions tab for detailed error messages
