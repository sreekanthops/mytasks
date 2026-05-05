# Jira Integration Guide

## Overview
This application now supports Jira integration, allowing you to view and manage your Jira issues directly from the task dashboard.

## Setup Instructions

### 1. Generate Jira API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Give it a name (e.g., "Task Dashboard")
4. Copy the generated token (you won't be able to see it again!)

**Important:** Use the **API Token** option, NOT OAuth with scopes. The API token is simpler and works with basic authentication.

### 2. Configure Jira Settings

1. Open your task dashboard
2. Navigate to **Settings** page
3. Scroll down to **Jira Configuration** section
4. Fill in the following fields:
   - **Jira URL**: Your Atlassian instance URL (e.g., `https://your-domain.atlassian.net`)
   - **Jira Email**: The email address associated with your Jira account
   - **Jira API Token**: Paste the API token you generated
   - **Default Project Key** (Optional): Your project key (e.g., `PROJ`, `DEV`)
5. Click **Save Jira Settings**

### 3. Access Jira Issues

1. Click on **Jira Issues** in the sidebar navigation
2. Use the dropdown to filter by status:
   - **Open Issues**: To Do, Open, Backlog
   - **In Progress**: In Progress, In Review
   - **Done**: Done, Closed, Resolved
3. Click **Refresh** to reload issues

## Features

### View Jira Issues
- See all your assigned Jira issues
- Filter by status (Open, In Progress, Done)
- View issue details including:
  - Issue key and summary
  - Status and priority
  - Issue type
  - Description preview
  - Last updated date

### Create Tasks from Jira
- Click **"Add to Tasks"** button on any Jira issue
- Automatically creates a task with:
  - Issue key and title
  - Full description
  - Link to Jira issue
  - Priority level

### Priority Badges
Issues are color-coded by priority:
- 🔴 **Highest/High**: Red badge
- 🟡 **Medium**: Orange badge
- 🔵 **Low/Lowest**: Blue badge

## API Endpoints

### Get Jira Issues
```
GET /api/jira/issues?status=open
```
Parameters:
- `status`: open, in_progress, or done

### Create Task from Jira
```
POST /api/tasks/from-jira/{issue_key}
```

## Troubleshooting

### "Jira not configured" Error
- Make sure you've saved your Jira settings in the Settings page
- Verify your Jira URL is correct (should include https://)
- Check that your API token is valid

### "Connection error" or API Errors
- Verify your Jira URL is accessible
- Check that your email and API token are correct
- Ensure your API token has not expired
- Make sure you have permission to view the issues

### No Issues Showing
- Check if you have any issues assigned to you in Jira
- Verify the project key is correct (if specified)
- Try different status filters
- Check your Jira permissions

## Security Notes

- API tokens are stored securely in the database
- Tokens are never displayed in the UI after saving
- Use environment variables for production deployments
- Regularly rotate your API tokens for security

## Database Schema

The following fields were added to the `Settings` model:
- `jira_url`: Your Jira instance URL
- `jira_email`: Email for authentication
- `jira_api_token`: API token for authentication
- `jira_project_key`: Default project filter

## Support

For issues or questions:
1. Check the Jira API documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
2. Verify your API token at: https://id.atlassian.com/manage-profile/security/api-tokens
3. Review the application logs for detailed error messages