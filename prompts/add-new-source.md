# prompt: add-new-source
> Copy-paste this prompt when asking Claude to add support for a new novel website.

---

```
Execute the add-source skill.

Target site: [site name, e.g. "wuxiaworld.com"]
Example novel URL: [paste a full URL to a novel index page]
Example chapter URL: [paste a full URL to a single chapter]

Site notes:
- [ ] Requires JavaScript rendering (Playwright)
- [ ] Uses standard HTML (requests + BeautifulSoup)
- [ ] Requires login / cookies
- [ ] Has pagination on the chapter list
- [ ] Known rate limiting / bot protection

Additional context:
[Any other details about the site structure, login requirements, or quirks you've noticed]
```
