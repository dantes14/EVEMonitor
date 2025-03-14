using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.ImageProcessing.Services;
using EVEMonitor.OCR.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Moq;
using Xunit;

namespace EVEMonitor.OCR.Tests
{
    public class OcrServiceTests
    {
        private readonly Mock<ILogger<OcrService>> _mockLogger;
        private readonly Mock<IConfigService> _mockConfigService;
        private readonly string _testDataPath;
        private readonly OcrService _ocrService;
        private readonly string _testImagesPath;
        private readonly string _tessdataPath;
        private readonly AppConfig _testConfig;

        public OcrServiceTests()
        {
            _mockLogger = new Mock<ILogger<OcrService>>();
            _mockConfigService = new Mock<IConfigService>();

            string? assemblyLocation = Path.GetDirectoryName(typeof(OcrServiceTests).Assembly.Location);
            _testDataPath = assemblyLocation != null
                ? Path.Combine(assemblyLocation, "TestData")
                : Path.Combine(Directory.GetCurrentDirectory(), "TestData");

            // 设置测试图像和tessdata路径
            _testImagesPath = Path.Combine(_testDataPath, "TestImages");
            _tessdataPath = Path.Combine(_testDataPath, "tessdata");

            _testConfig = new AppConfig
            {
                DangerousShipTypes = new List<string>
                {
                    "泰坦",
                    "超级航母",
                    "Battleship",
                    "Carrier",
                    "Dreadnought"
                },
                DangerousCorporations = new List<string>
                {
                    "黑军团",
                    "死亡军团",
                    "Evil Corp",
                    "Bad Guys Inc"
                }
            };

            _mockConfigService.Setup(x => x.CurrentConfig).Returns(_testConfig);
            _ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);
        }

        [Fact]
        public void Constructor_ShouldInitializeCorrectly()
        {
            // Arrange & Act
            var ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);

            // Assert
            Assert.NotNull(ocrService);
        }

        [Fact]
        public void RecognizeSystemName_WithValidImage_ShouldReturnSystemName()
        {
            // 此测试需要有效的测试图像
            // 在实际测试中，应该使用包含已知系统名称的图像

            // Arrange
            var ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);
            string testImagePath = Path.Combine(_testImagesPath, "system_name_sample.png");

            // 如果测试图像不存在，跳过测试
            if (!File.Exists(testImagePath))
            {
                return;
            }

            using (var bitmap = new Bitmap(testImagePath))
            {
                // Act
                string systemName = ocrService.RecognizeSystemName(bitmap);

                // Assert
                Assert.NotNull(systemName);
                Assert.NotEmpty(systemName);
            }
        }

        [Fact]
        public void RecognizeShipTable_WithValidImage_ShouldReturnShipList()
        {
            // 此测试需要有效的测试图像
            // 在实际测试中，应该使用包含舰船表格的图像

            // Arrange
            var mockImageProcessingLogger = new Mock<ILogger<ImageProcessingService>>();
            var imageProcessingService = new ImageProcessingService(mockImageProcessingLogger.Object, _mockConfigService.Object);
            var ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);

            string testImagePath = Path.Combine(_testImagesPath, "ship_table_sample.png");

            // 如果测试图像不存在，跳过测试
            if (!File.Exists(testImagePath))
            {
                return;
            }

            using (var bitmap = new Bitmap(testImagePath))
            {
                // Act
                List<ShipInfo> ships = ocrService.RecognizeShipTable(bitmap);

                // Assert
                Assert.NotNull(ships);
            }
        }

        [Fact]
        public void ProcessRecognitionResult_ShouldReturnCorrectResult()
        {
            // Arrange
            var mockImageProcessingLogger = new Mock<ILogger<ImageProcessingService>>();
            var imageProcessingService = new ImageProcessingService(mockImageProcessingLogger.Object, _mockConfigService.Object);
            var ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);

            int emulatorIndex = 0;
            string systemName = "吉他";
            var ships = new List<ShipInfo>
            {
                new ShipInfo
                {
                    Name = "测试舰船",
                    Type = "巡洋舰",
                    Corporation = "测试公司",
                    Distance = 10.5,
                    IsDangerous = false
                }
            };

            // Act
            var result = ocrService.ProcessRecognitionResult(emulatorIndex, systemName, ships);

            // Assert
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.Equal(systemName, result.SystemName);
            Assert.Equal(ships.Count, result.Ships.Count);
            Assert.False(result.ContainsDangerousShips);
        }

        [Fact]
        public void ProcessRecognitionResult_WithDangerousShip_ShouldFlagAsDangerous()
        {
            // Arrange
            var mockImageProcessingLogger = new Mock<ILogger<ImageProcessingService>>();
            var imageProcessingService = new ImageProcessingService(mockImageProcessingLogger.Object, _mockConfigService.Object);
            var ocrService = new OcrService(_mockLogger.Object, _mockConfigService.Object);

            int emulatorIndex = 0;
            string systemName = "吉他";
            var ships = new List<ShipInfo>
            {
                new ShipInfo
                {
                    Name = "危险舰船",
                    Type = "泰坦",
                    Corporation = "黑军团",
                    Distance = 10.5,
                    IsDangerous = true
                }
            };

            // Act
            var result = ocrService.ProcessRecognitionResult(emulatorIndex, systemName, ships);

            // Assert
            Assert.Equal(emulatorIndex, result.EmulatorIndex);
            Assert.Equal(systemName, result.SystemName);
            Assert.Equal(ships.Count, result.Ships.Count);
            Assert.True(result.ContainsDangerousShips);
        }
    }
}