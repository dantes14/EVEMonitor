# 贡献指南

感谢你对EVEMonitor项目的关注！我们欢迎任何形式的贡献，包括但不限于：提交bug报告、新功能建议、文档改进、代码贡献等。

## 行为准则

本项目采用[贡献者公约](https://www.contributor-covenant.org/version/2/0/code_of_conduct/)。参与本项目即表示你同意遵守此公约。

## 如何贡献

### 提交Issue

1. 在提交Issue之前，请先搜索是否已经存在类似的问题
2. 使用提供的Issue模板（bug报告或功能建议）
3. 提供尽可能详细的信息，包括：
   - 问题描述
   - 重现步骤
   - 环境信息
   - 相关日志
   - 截图（如果适用）

### 提交Pull Request

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个Pull Request

### 开发流程

1. 克隆仓库
```bash
git clone https://github.com/dantes14/EVEMonitor.git
cd EVEMonitor
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. 运行测试
```bash
pytest tests/ -v
```

### 代码风格

- 遵循PEP 8规范
- 使用类型注解
- 添加适当的文档字符串
- 保持代码简洁清晰

### 提交信息规范

提交信息应该清晰描述改动内容，格式如下：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

### 分支管理

- main: 主分支，保持稳定
- develop: 开发分支
- feature/*: 新功能分支
- bugfix/*: 修复bug分支
- release/*: 发布分支

## 文档贡献

- 确保文档清晰易懂
- 添加适当的示例
- 更新相关文档
- 检查拼写和语法

## 测试贡献

- 为新功能添加单元测试
- 确保所有测试通过
- 保持测试覆盖率
- 添加集成测试（如果需要）

## 发布流程

1. 更新版本号
2. 更新CHANGELOG.md
3. 创建发布标签
4. 生成发布说明

## 联系方式

如果你有任何问题或建议，可以通过以下方式联系我们：

- 提交Issue
- 发送邮件到：[你的邮箱]

感谢你的贡献！ 