# Tesseract 数据文件

这个目录用于存放Tesseract OCR引擎所需的语言数据文件。

## 所需文件

为了运行OCR测试，您需要下载以下文件并放置在此目录中：

1. `eng.traineddata` - 英语语言数据
2. `chi_sim.traineddata` - 简体中文语言数据

## 获取数据文件

您可以从以下地址下载Tesseract语言数据文件：

- 官方GitHub仓库：https://github.com/tesseract-ocr/tessdata
- 或者从Tesseract官方网站：https://tesseract-ocr.github.io/tessdoc/Data-Files.html

## 注意事项

- 确保下载的文件版本与您使用的Tesseract版本兼容
- 测试运行前，请确保这些文件已正确放置在此目录中
- 如果没有这些数据文件，OCR相关的测试将会失败