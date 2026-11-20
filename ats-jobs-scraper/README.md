# ATS Jobs Scraper: Greenhouse, Lever, Ashby, SmartRecruiters, Recruitee & Workable

Get **every open job** from company careers pages in one clean, consistent format. The scraper reads each platform's official public job-board feed, so runs are fast, cheap and don't break when page layouts change.

## What it does
- Paste careers-page URLs or company slugs, e.g. `https://boards.greenhouse.io/airbnb`, `https://jobs.lever.co/palantir`, `https://jobs.ashbyhq.com/openai`, or just `stripe`.
- Plain slugs are checked on **every** supported platform automatically.
- Filter by title keywords, location, remote, and how recently jobs were posted.
- Output uses **one schema for all platforms**, ready for spreadsheets, job boards, alerts and lead generation.

## Supported platforms
| Platform | Example URL |
|---|---|
| Greenhouse | boards.greenhouse.io/airbnb, job-boards.greenhouse.io/airbnb |
| Lever | jobs.lever.co/palantir (US & EU) |
| Ashby | jobs.ashbyhq.com/openai (includes salary ranges when published) |
| SmartRecruiters | jobs.smartrecruiters.com/BoschGroup |
| Recruitee | company.recruitee.com |
| Workable | apply.workable.com/company |

## Output example
```json
{
  "platform": "ashby",
  "company": "openai",
  "jobId": "4f2c...",
  "title": "Software Engineer, Applied AI",
  "department": "Applied AI",
  "location": "San Francisco",
  "remote": false,
  "employmentType": "FullTime",
  "salary": "$310K – $460K",
  "postedAt": "2026-11-12T18:03:11.000Z",
  "url": "https://jobs.ashbyhq.com/openai/4f2c...",
  "applyUrl": "https://jobs.ashbyhq.com/openai/4f2c.../application",
  "descriptionText": "..."
}
```

## Use cases
- Build a niche job board or newsletter
- Hiring-signal lead generation (who is hiring sales, engineers, etc.)
- Competitor and market hiring analysis
- Daily job alerts (schedule the Actor and connect a webhook, Slack or Google Sheets)

## Pricing
Pay only for results: **$1.50 per 1,000 jobs**. No subscription, no proxies needed.

## Tips
- Find a company's slug in its careers URL (the part after the platform domain).
- Schedule a daily run with `postedWithinDays: 1` for fresh-jobs alerts.
