# EVE监视器测试指南

本文档提供了EVE监视器在Windows环境下的测试流程和最佳实践。

## 目录
1. [测试环境准备](#测试环境准备)
2. [单元测试](#单元测试)
3. [功能测试](#功能测试)
4. [集成测试](#集成测试)
5. [性能测试](#性能测试)
6. [测试中的常见问题](#测试中的常见问题)

## 测试环境准备

### 安装测试依赖

```cmd
# 激活虚拟环境
venv\Scripts\activate

# 安装测试依赖
pip install -r requirements-dev.txt
```

### 测试数据准备

为了确保测试的一致性，我们提供了一系列测试数据：

1. **测试图像**：在`tests/data/images`目录下包含各种测试用的截图
2. **配置文件**：在`tests/data/configs`目录下包含不同场景的配置文件
3. **模拟OCR结果**：在`tests/data/ocr_results`目录下包含预定义的OCR识别结果

## 单元测试

EVE监视器使用pytest进行单元测试。运行单元测试：

```cmd
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_ocr_engine.py

# 运行带有特定标记的测试
pytest -m "ocr"

# 显示详细输出
pytest -v
```

### 测试覆盖率检查

```cmd
# 生成覆盖率报告
pytest --cov=src tests/

# 生成HTML格式的覆盖率报告
pytest --cov=src --cov-report=html tests/
```

## 功能测试

### OCR引擎测试

测试OCR引擎在不同场景下的识别效果：

```cmd
# 运行OCR引擎测试
python -m tests.manual.test_ocr_manual

# 使用特定图像测试
python -m tests.manual.test_ocr_manual --image tests/data/images/ship_status.png

# 对比不同OCR引擎
python -m tests.manual.test_ocr_manual --engines paddle,tesseract
```

### 屏幕捕获测试

测试不同窗口和区域的屏幕捕获功能：

```cmd
# 运行屏幕捕获测试
python -m tests.manual.test_capture_manual

# 使用特定窗口标题
python -m tests.manual.test_capture_manual --window "EVE Online"
```

### UI界面测试

测试用户界面功能：

```cmd
# 运行UI测试
python -m tests.manual.test_ui_manual
```

## 集成测试

集成测试验证系统各组件的协同工作。

```cmd
# 运行基础集成测试
pytest tests/integration/

# 全系统测试（需要模拟游戏窗口）
python -m tests.integration.test_full_system
```

## 性能测试

性能测试评估系统在不同负载下的表现。

```cmd
# 运行性能测试套件
python -m tests.performance.test_performance

# 截图性能测试
python -m tests.performance.test_capture_performance --iterations 100

# OCR性能测试
python -m tests.performance.test_ocr_performance --iterations 50 --engine paddle
```

## 测试中的常见问题

### 1. Tesseract测试失败

**问题**：使用Tesseract的OCR测试失败，错误提示"未找到Tesseract路径"

**解决方案**：
- 确保Tesseract已正确安装
- 在测试前设置环境变量：`set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`
- 或修改测试fixture中的配置初始化代码，提供正确的Tesseract路径

### 2. PaddleOCR测试问题

**问题**：PaddleOCR测试初始化缓慢或失败

**解决方案**：
- 第一次运行PaddleOCR测试会下载模型，可能需要较长时间
- 确保网络连接良好，或手动下载模型放置到指定目录
- 使用`@pytest.mark.skipif`标记跳过特定环境下的PaddleOCR测试

### 3. 窗口捕获测试失败

**问题**：窗口捕获测试找不到指定窗口

**解决方案**：
- 确保测试前已打开目标窗口
- 使用`--window`参数指定实际存在的窗口标题
- 考虑使用模拟窗口进行测试

### 4. 多线程相关测试失败

**问题**：涉及多线程的测试随机失败

**解决方案**：
- 使用`time.sleep()`增加等待时间
- 优化测试中的线程同步机制
- 对不稳定的测试使用`@pytest.mark.flaky(reruns=3)`标记尝试多次运行

## 自动化测试集成

EVE监视器支持与CI/CD系统集成进行自动化测试：

```yaml
# .github/workflows/tests.yml示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest tests/
```

## 测试报告

测试完成后，建议生成全面的测试报告：

```cmd
# 生成XML格式测试报告
pytest --junitxml=test-reports/results.xml

# 生成HTML格式测试报告
pytest --html=test-reports/report.html
```

---

如有任何问题或建议，请联系项目开发团队。 