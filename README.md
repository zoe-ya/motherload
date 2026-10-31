# motherload

Mothering 2027 edition: tools I build to make it easier organizing kids at home.

## Projects

| Project | What it is |
|---|---|
| [Kid Start Page](kid-start-page/) | A home page for my kids with daily tasks, a visual timer, a weekly Bible verse, and a parent page for me to update it all. Great to keep everyone organized after school, or homeschool. **[Try the demo](https://zoe-ya.github.io/motherload/)** |

---

## Start Page

👉 **[Try the live demo](https://zoe-ya.github.io/motherload/)**: no install needed. Anything you change is saved only in your own browser.

A home page for my two school aged kids. One computer in the house runs it, and each kid's browser opens it as their home page over our home Wi‑Fi. Nothing goes on the internet.

### What the kids see

- **Big clock and date**, always on screen.
- **Today's tasks** to check off. Each one turns into a gold coin or emerald block, with a sound and a progress bar. Finishing them all shows "LEVEL COMPLETE!"
- **Visual timer** with 15, 25, 30 and 45 minute presets. The time left is a shrinking colored wedge, with a new color every 10 minutes (purple, blue, green, yellow, orange, red), so they can see how much time is left at a glance. A **Big** button fills the screen with it.
- **Verse of the Week** from a list of 52 verses, one for each week of the year.
- **Happening Today** and **Reminders**. Links added to these become buttons that open in a new tab.
- **This Week**: the next 7 days, including weekly things like soccer and piano practice. Finished tasks get crossed off.
- **Doodle Pad** with colors, a rainbow pen, emoji stamps, an eraser, undo, and saving the drawing as a picture.
- **Three looks** each kid can switch between: ⛏️ **Block World** (stone, grass and dirt), 🍄 **Jump World** (bricks, hills, flowers and buzzing bees) and 📐 **Blueprint** (hand-drawn blue ink on grey graph paper, for older kids).

### What the parent gets

- Add **tasks, reminders and events** for one kid or both, for one day, certain days every week, or every day.
- **Rearrange the page** by dragging widgets between the left column, right column, full width, or hidden.
- See **today's progress** for each kid.
- Set names, emoji and favorite colors, plus a **PIN** so the kids can't edit.

### Set it up for your family

0. **Have Grok or Claude do it for you.** Or DIY:
1. **Install Python 3** from [python.org](https://www.python.org/downloads/). On Windows, check **"Add Python to PATH"** during install.
2. **Download this project:** click the green **Code** button on GitHub, choose **Download ZIP**, and unzip it.
3. **Start it** on the computer that will host it (it needs to stay on):
   - Windows: open the `kid-start-page` folder and double-click `Kid Start Page.bat`. If Windows Firewall asks, allow **Private networks** only.
   - Mac: open Terminal in the `kid-start-page` folder and run `python3 server.py`.
4. **Set it up as the parent:** on that computer, go to `http://localhost:8080/parent`. Set a PIN, your kids' names and colors, and add their tasks.
5. **Open it on each kid's device** (same Wi‑Fi): go to `http://<host-computer-address>:8080/?kid=1` (or `?kid=2`). The address is the host's **IPv4 Address**, found by running `ipconfig` (Windows) or in System Settings → Network (Mac). It usually starts with `192.168.`.
   - On a laptop or desktop, make that link the browser's home page.
   - On an iPad, open it in Safari, then **Share → Add to Home Screen**.
6. **Optional, start automatically:** on Windows, press `Win + R`, type `shell:startup`, and put a shortcut to `Kid Start Page.bat` in that folder.

It only works on your home Wi‑Fi, and nothing is sent to the internet.

The first run creates `data.json` with some starter items. That file holds your PIN and your kids' info, so it's left out of git.

### Weekly verses

`kid-start-page/52.bible.verses.txt` has one verse per line, written as `verse text — Reference`. Week 1 of the year shows line 1, week 2 shows line 2, and so on. Swap in your own verses any time.

Scripture quotations taken from The Holy Bible, New International Version® NIV®. Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.™ Used by permission. All rights reserved worldwide.

### How it's built

- `server.py` is a small Python web server that saves to `data.json`.
- `web/index.html` is the kid page, `web/parent.html` is the parent page, and `web/common.js` is shared code.
- `web/theme.css` and `web/themes.css` hold the two looks.
