# Codex 聊天标题的来源与自定义命名

核对日期：2026-11-05  
分类：计算机与工具 → Codex

**公开代码存在用最早用户消息生成初始标题和预览的路径；我们采用理解主题后主动重命名的方式，使用“分类：主题”。**

## 本篇学习重点

- **建议掌握**：预览与名称不同；助手改名约定没有改变应用默认算法。
- **用时查阅**：源码行号、接口参数和命名操作。
- **可以要求 Codex**：主题明确后按分类与主题命名，并回读确认保存结果。

## 默认标题为什么像开场白

源码中，标题为空时会将去掉包装前缀的用户消息设为标题，最早的消息也用于预览。这段路径没有调用模型总结主题。[存储层代码](https://github.com/openai/codex/blob/5112ce6edeb95f2296a5ffec47dbab4764e65853/codex-rs/state/src/extract.rs#L191-L208)

命令行聊天列表优先显示明确设置的名称，否则显示预览，然后根据可用宽度截短。[名称选择](https://github.com/openai/codex/blob/5112ce6edeb95f2296a5ffec47dbab4764e65853/codex-rs/tui/src/resume_picker.rs#L1282-L1284) · [显示截断](https://github.com/openai/codex/blob/5112ce6edeb95f2296a5ffec47dbab4764e65853/codex-rs/tui/src/resume_picker.rs#L3310-L3313)

这些证据说明公开存储层与命令行的行为，不足以证明所用桌面版本的全部标题生成逻辑都相同。最初直接说“桌面端就是截取第一句话”过于确定，应保留这个边界。

## 我选择的命名方式

- `学习库：知识整理与维护`
- `Python：中文乱码与环境变量`
- `Git：多任务 worktree 协作`

新聊天主题明确后命名一次；用户指定的标题优先，主题没有明显变化就不反复修改。

## 怎样让标题落地

优先使用应用提供的标题工具；缺失时检查官方 `thread/name/set`。本机 schema 已确认参数为 `threadId` 和 `name`，设置后用 `thread/read` 回读名称。[官方接口](https://learn.chatgpt.com/docs/app-server)

本聊天已成功改名为“学习库：知识整理与维护”。偏好已写入全局 AGENTS.md；这属于助手执行的约定，没有修改应用内置标题算法，也没有后台定时改名程序。新聊天是否主动执行还需要验收。

## 回顾问题

- 内容预览和明确设置的聊天名称有什么区别？
- 全局命名约定是否等于改变应用默认命名算法？

## 来源

- 原始讨论与本机验证（私人资料，未公开）
- [官方标题建议](https://learn.chatgpt.com/docs/projects#organize-projects-and-chats)
