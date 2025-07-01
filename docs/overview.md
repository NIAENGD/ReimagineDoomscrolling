# Project ReimagineDoomscrolling

This document describes a proposed redesign of the abandoned project for curating YouTube content.

## Goals
- Surface higher quality and more enjoyable videos from a user's feed
- Reduce reliance on noisy keyword searches
- Provide automatic scoring and article-style transcripts for each video

## Architecture Overview
The new application consists of a local helper server and a browser extension.

### Browser Extension
- Provides a control panel where the user can start or stop analysis, choose the number of videos to process and configure prompts.
- Opens two hidden tabs: one for YouTube and one for ChatGPT. Both tabs share the user's logged-in cookies.
- Collects video links from the YouTube feed by scrolling until the desired number of items is gathered, excluding Shorts, ads and other irrelevant entries.

### Local Helper Server
- Runs Whisper for speech-to-text when subtitle tracks are unavailable.
- Hosts a small web interface to view analysed videos and their rewritten articles.
- Communicates with the extension to receive audio snippets and return transcripts.

### Processing Steps
1. Extension gathers video links and downloads official subtitles using `yt-dlp`. If no subtitles exist, it retrieves audio and requests transcription from the local server.
2. Each transcript is sent to ChatGPT twice: first to score the video using several criteria, then to rewrite it as a full article in the style of the original creator.
3. Results are stored locally and served on a web page sorted by total score. Users can read each article, like or dislike it and optionally trigger an automated watch-through/feedback action in the hidden YouTube tab.

## Default Prompts
### Scoring
```
预处理-忽略所有广告部分，并不以此为依据处理视频

视频类别：【写出类别】
类别评分：【从列表中选择，每个用一句话简要解释原因】

逻辑：混乱，误导性，清晰
深度：阐述，起因，深层，底层
见解：粗浅，深层，底层
表达：呆板、自然、生动
启发性：中性、有启发、强激励

综合质量分：【0-100，极为严格的分数，平庸视频不会超过30，极佳的视频可能到60，没有视频能达到100】

盲点与挑战：提炼内容，指出潜在误导、局限、偏颇或易被误解之处，含信息来源、现实可行性、商业倾向、风险遗漏等方面，一句话说完，简洁理性，勿泛泛而谈。
```

### Rewriting Transcript as Article
```
以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加任何旁人评价或个人观点。
标题/小标题分明，段落清晰；语言优美自然，贴合原风格。
原汁原味还原引用、比喻、故事、幽默等表现手法；保持视频作者的个性（如讽刺、深情等）。
开头简要介绍视频内容，结尾收束主要结论或号召；绝不提及“视频”，直接以文章形式呈现。
切记！这并不是一个TLDR，或是总结，而是完整的文稿。
切记！这不是一个总结，你需要输出尽量还原原视频的长度。
```

---
This document should serve as a starting point for future development of the extension and helper server.
