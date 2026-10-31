# Rocky Hock Baptist Church website

The public website for Rocky Hock Baptist Church, 113 Rocky Hock Church Road, Edenton, NC.

## How it’s organized

| Folder | What’s in it |
|---|---|
| `index.html` | The website itself (all pages) |
| `data/site.json` | Editable content: events, banners, alert, weekly schedule, staff, special events, careers, photo captions, bulletin and newsletter lists |
| `bulletins/` | Weekly bulletin PDFs |
| `newsletters/` | Monthly newsletter PDFs |
| `photos/` | Photo gallery pictures |
| `staff/` | Staff photos |
| `files/` | Other PDFs (league rules, job descriptions, flyers) |
| `images/` | Site images such as the logo |

## Editing the site

Staff edit the site from the website itself: scroll to the bottom of any page, click **Staff sign in**, paste a sign-in key, and use the edit buttons. Pressing **Save changes** updates `data/site.json`; uploads go into the folders above. The public site refreshes about a minute after each save.

A sign-in key is a GitHub *fine-grained personal access token* limited to the `hctynch/rhbc-website` repository with **Contents: Read and write** permission.
