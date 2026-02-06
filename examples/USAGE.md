# Quarto MCP Server - 使用例

## 基本的な使用例

### HTMLへの変換

```json
{
  "name": "quarto_render",
  "arguments": {
    "content": "# My Document\n\nThis is a test document.",
    "format": "html",
    "output_path": "/tmp/output.html"
  }
}
```

### PowerPointへの変換

```json
{
  "name": "quarto_render",
  "arguments": {
    "content": "# Presentation\n\n## Slide 1\n\nContent here...",
    "format": "pptx",
    "output_path": "/tmp/presentation.pptx"
  }
}
```

### PowerPoint（テンプレート付き）への変換

```json
{
  "name": "quarto_render",
  "arguments": {
    "content": "# Corporate Presentation\n\n## Overview\n\n- Point 1\n- Point 2",
    "format": "pptx",
    "output_path": "/tmp/corporate.pptx",
    "template": "corporate_standard"
  }
}
```

### PowerPoint（カスタムオプション付き）への変換

```json
{
  "name": "quarto_render",
  "arguments": {
    "content": "# Advanced Presentation\n\n## Features\n\nAdvanced features...",
    "format": "pptx",
    "output_path": "/tmp/advanced.pptx",
    "format_options": {
      "slide-level": 2,
      "toc": true
    }
  }
}
```
